import { useEffect, useRef, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import * as d3 from 'd3'
import { selectReport, selectTransactions } from '../store/fraudSlice'
import { setSelectedNode } from '../store/uiSlice'
import { buildLookups, buildGraphData, RING_COLORS, NODE_RADIUS, HALO_RADIUS } from '../utils/graphHelpers'
import NodeDetailPanel from './NodeDetailPanel'

/* ─────────────────────────────────────────────────────────────────────────────
   GRAPH FIX — why nodes appeared in disconnected "islands":
   ─────────────────────────────────────────────────────────────────────────────
   D3 forceSimulation only connects nodes that share a link. Nodes with NO
   edges to the main cluster drift to wherever they were initialised (random).
   The fix is a combination of:
     1. forceX / forceY  — weak magnetic pull every node toward canvas centre
     2. Higher negative charge — pushes clusters apart but keeps them on screen
     3. Collision radius — prevents label overlaps that create visual "gaps"
     4. alphaDecay / velocityDecay tweaks — longer warm-up so clusters merge
   This guarantees ONE unified layout regardless of graph connectivity.
   ───────────────────────────────────────────────────────────────────────────── */

export default function GraphPanel() {
  const dispatch     = useDispatch()
  const report       = useSelector(selectReport)
  const transactions = useSelector(selectTransactions)
  const containerRef = useRef(null)
  const svgRef       = useRef(null)
  const simRef       = useRef(null)

  // ── Build the graph whenever report/txns arrive ──────────────────────────
  const buildGraph = useCallback(() => {
    const el = containerRef.current
    if (!el || !report || transactions.length === 0) return

    // Measure container — important: must be done after layout
    const W = el.clientWidth
    const H = el.clientHeight
    if (W === 0 || H === 0) return

    // Kill old simulation
    if (simRef.current) { simRef.current.stop(); simRef.current = null }

    // Clear old SVG
    d3.select(el).selectAll('*').remove()

    // Build data
    const lookups = buildLookups(report)
    const { suspMap, ringMap, ringEdgeMap } = lookups
    const { nodes, links } = buildGraphData(transactions, lookups)

    // ── SVG setup ────────────────────────────────────────────────────────
    const svg = d3
      .select(el)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${W} ${H}`)
      .attr('class', 'graph-svg')
      .style('background', 'transparent')
      .style('display', 'block')

    svgRef.current = svg

    // ── Defs: filters + arrowheads ────────────────────────────────────────
    const defs = svg.append('defs')

    // Glow filter for ring nodes
    const glowF = defs
      .append('filter')
      .attr('id', 'glow')
      .attr('x', '-60%').attr('y', '-60%')
      .attr('width', '220%').attr('height', '220%')
    glowF.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '5').attr('result', 'blur')
    const gM = glowF.append('feMerge')
    gM.append('feMergeNode').attr('in', 'blur')
    gM.append('feMergeNode').attr('in', 'SourceGraphic')

    // Soft glow for suspicious nodes
    const softF = defs
      .append('filter')
      .attr('id', 'softglow')
      .attr('x', '-40%').attr('y', '-40%')
      .attr('width', '180%').attr('height', '180%')
    softF.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '3').attr('result', 'blur')
    const sM = softF.append('feMerge')
    sM.append('feMergeNode').attr('in', 'blur')
    sM.append('feMergeNode').attr('in', 'SourceGraphic')

    // Arrow markers
    const mkArrow = (id, color, refX = 22) =>
      defs
        .append('marker')
        .attr('id', id)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', refX)
        .attr('refY', 0)
        .attr('markerWidth', 5)
        .attr('markerHeight', 5)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color)

    mkArrow('arr-normal', '#10B981')
    mkArrow('arr-susp',   '#F59E0B')
    RING_COLORS.forEach((col, i) => mkArrow(`arr-ring-${i}`, col))

    // ── Simulation — THE KEY FIX ──────────────────────────────────────────
    const cx = W / 2
    const cy = H / 2

    const simulation = d3
      .forceSimulation(nodes)
      // Links pull connected nodes together
      .force(
        'link',
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance((d) => {
            // Ring-to-ring edges stay tight
            const sk = `${d.source.id || d.source}→${d.target.id || d.target}`
            return ringEdgeMap[sk] ? 60 : 100
          })
          .strength((d) => {
            const sk = `${d.source.id || d.source}→${d.target.id || d.target}`
            return ringEdgeMap[sk] ? 0.9 : 0.5
          })
      )
      // Repulsion between nodes
      .force('charge', d3.forceManyBody().strength(-320).distanceMax(350))
      // ★ THE FIX: forceX + forceY pulls EVERY node toward the canvas centre.
      //   Even isolated nodes that share no edge get pulled in, so there are
      //   no disconnected islands floating off-screen.
      .force('x', d3.forceX(cx).strength(0.08))
      .force('y', d3.forceY(cy).strength(0.08))
      // Collision prevents node overlap (which looked like "gaps")
      .force(
        'collide',
        d3.forceCollide().radius((d) => {
          if (d.ring) return NODE_RADIUS.ring + 18
          if (d.susp) return NODE_RADIUS.susp + 14
          return NODE_RADIUS.normal + 10
        }).strength(0.8)
      )
      .alphaDecay(0.015)       // slower cool-down → better convergence
      .velocityDecay(0.35)     // more damping → less jitter

    simRef.current = simulation

    // ── Zoomable group ────────────────────────────────────────────────────
    const g = svg.append('g')

    svg.call(
      d3
        .zoom()
        .scaleExtent([0.15, 8])
        .on('zoom', (e) => g.attr('transform', e.transform))
    )

    // Click on background → deselect
    svg.on('click', () => dispatch(setSelectedNode(null)))

    // ── Edges ─────────────────────────────────────────────────────────────
    const edgeGroup = g.append('g').attr('class', 'edges')

    const edge = edgeGroup
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-opacity', 0.7)
      .attr('stroke-width', (d) => {
        const k = `${d.source.id || d.source}→${d.target.id || d.target}`
        return ringEdgeMap[k] ? 2.5 : 1.2
      })
      .attr('stroke', (d) => {
        const src = d.source.id || d.source
        const tgt = d.target.id || d.target
        const k   = `${src}→${tgt}`
        if (ringEdgeMap[k]) return ringEdgeMap[k]
        if (suspMap[src])   return '#F59E0B'
        return '#10B981'
      })
      .attr('marker-end', (d) => {
        const src = d.source.id || d.source
        const tgt = d.target.id || d.target
        const k   = `${src}→${tgt}`
        if (ringEdgeMap[k]) {
          // Use the ring color's arrow
          const ringIdx = report.fraud_rings.findIndex(
            (r) =>
              r.member_accounts.includes(src) &&
              r.member_accounts.includes(tgt)
          )
          return `url(#arr-ring-${Math.max(0, ringIdx) % RING_COLORS.length})`
        }
        if (suspMap[src]) return 'url(#arr-susp)'
        return 'url(#arr-normal)'
      })

    // ── Nodes ─────────────────────────────────────────────────────────────
    const nodeGroup = g.append('g').attr('class', 'nodes')

    const nodeEl = nodeGroup
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(
        d3
          .drag()
          .on('start', (ev, d) => {
            if (!ev.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (ev, d) => {
            d.fx = ev.x
            d.fy = ev.y
          })
          .on('end', (ev, d) => {
            if (!ev.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )
      .on('click', (ev, d) => {
        ev.stopPropagation()
        // Serialize only what NodeDetailPanel needs
        dispatch(
          setSelectedNode({
            id:    d.id,
            susp:  d.susp,
            ring:  d.ring,
            score: d.score,
          })
        )
      })

    // Outer halo ring (ring members only)
    nodeEl
      .filter((d) => !!d.ring)
      .append('circle')
      .attr('r', HALO_RADIUS)
      .attr('fill', 'none')
      .attr('stroke', (d) => d.ring.col)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.35)
      .attr('filter', 'url(#glow)')

    // Main circle
    nodeEl
      .append('circle')
      .attr('r',   (d) => (d.ring ? NODE_RADIUS.ring : d.susp ? NODE_RADIUS.susp : NODE_RADIUS.normal))
      .attr('fill', (d) => {
        if (d.ring) return d.ring.col + '33'
        if (d.susp) return '#F59E0B' + '22'
        return '#252A32'
      })
      .attr('stroke',       (d) => (d.ring ? d.ring.col : d.susp ? '#F59E0B' : '#10B981'))
      .attr('stroke-width', (d) => (d.ring ? 2.5 : 1.5))
      .attr('filter',       (d) => (d.ring ? 'url(#glow)' : d.susp ? 'url(#softglow)' : 'none'))

    // Label
    nodeEl
      .append('text')
      .text((d) => (d.id.length > 12 ? d.id.slice(0, 11) + '…' : d.id))
      .attr('text-anchor', 'middle')
      .attr('y', (d) => (d.ring ? NODE_RADIUS.ring : d.susp ? NODE_RADIUS.susp : NODE_RADIUS.normal) + 14)
      .attr('fill',        (d) => (d.ring ? d.ring.col : d.susp ? '#F59E0B' : '#10B981'))
      .attr('font-size',   '9px')
      .attr('font-weight', (d) => (d.ring ? '700' : '400'))

    // ── Tick: update positions ────────────────────────────────────────────
    simulation.on('tick', () => {
      edge
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y)

      nodeEl.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })
  }, [report, transactions, dispatch])

  // Trigger build when data lands
  useEffect(() => {
    if (!report || transactions.length === 0) return
    // Wait for the DOM to fully paint the container before measuring
    const id = requestAnimationFrame(() => {
      setTimeout(buildGraph, 50)
    })
    return () => cancelAnimationFrame(id)
  }, [report, transactions, buildGraph])

  // Rebuild on resize
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(() => {
      if (report && transactions.length > 0) buildGraph()
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [report, transactions, buildGraph])

  // Cleanup simulation on unmount
  useEffect(() => () => { simRef.current?.stop() }, [])

  return (
    <div className="flex flex-1 min-h-0 border border-emerald-600/30 rounded-xl overflow-hidden bg-card shadow-lg shadow-emerald-600/10">
      {/* Canvas */}
      <div
        ref={containerRef}
        className="flex-1 relative overflow-hidden"
        style={{ minHeight: 520 }}
      >
        {/* Overlay legend */}
        <div className="absolute top-3 left-3 z-10 bg-surface/90 border border-emerald-600/30 rounded-lg px-3 py-2 backdrop-blur-sm">
          <p className="text-emerald-400 font-black tracking-widest mb-1" style={{ fontSize: 9 }}>
            TRANSACTION NETWORK GRAPH
          </p>
          <p className="text-muted" style={{ fontSize: 9, letterSpacing: '0.08em' }}>
            SCROLL = ZOOM &nbsp;·&nbsp; DRAG NODE = REPOSITION &nbsp;·&nbsp; CLICK NODE = DETAILS
          </p>
          <div className="flex gap-4 mt-2">
            <LegendDot color={RING_COLORS[0]} label="Fraud Ring" />
            <LegendDot color="#F59E0B"         label="Suspicious" />
            <LegendDot color="#10B981"         label="Normal" />
          </div>
        </div>

        {/* Ring color key */}
        {report?.fraud_rings?.length > 0 && (
          <div className="absolute bottom-3 left-3 z-10 bg-surface/90 border border-emerald-600/30 rounded-lg px-3 py-2 backdrop-blur-sm max-w-xs">
            <p className="text-muted tracking-widest mb-2" style={{ fontSize: 9 }}>RING COLOR KEY</p>
            {report.fraud_rings.map((r, i) => (
              <div key={r.ring_id} className="flex items-center gap-2 mb-1">
                <div
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: RING_COLORS[i % RING_COLORS.length] }}
                />
                <span className="font-black text-xs" style={{ color: RING_COLORS[i % RING_COLORS.length] }}>
                  {r.ring_id}
                </span>
                <span className="text-muted text-xs">· {r.member_accounts.length} accts</span>
                <span className="text-danger font-black text-xs ml-auto">⚠{r.risk_score}</span>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {(!report || transactions.length === 0) && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-muted">
              <p className="text-4xl mb-3">📊</p>
              <p className="text-sm tracking-widest">Upload a CSV and run analysis to see the graph</p>
            </div>
          </div>
        )}
      </div>

      {/* Node detail panel */}
      <NodeDetailPanel />
    </div>
  )
}

function LegendDot({ color, label }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-2 h-2 rounded-full" style={{ background: color }} />
      <span style={{ color, fontSize: 9 }}>{label}</span>
    </div>
  )
}
