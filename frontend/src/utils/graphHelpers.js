export const RING_COLORS = [
  '#ff2d55', '#ff6e00', '#ffaa00', '#c084fc',
  '#00c8ff', '#00e676', '#f472b6', '#34d399',
]

export const NODE_RADIUS = { ring: 14, susp: 11, normal: 7 }
export const HALO_RADIUS  = 24

/** Build lookup maps from a report object */
export function buildLookups(report) {
  const suspMap  = {}   // account_id → suspicious_account object
  const scoreMap = {}   // account_id → suspicion_score
  const ringMap  = {}   // account_id → { ring, col }
  const ringEdgeMap = {}// "src→tgt"  → color  (for any edge inside a ring)

  report.suspicious_accounts.forEach((a) => {
    suspMap[a.account_id]  = a
    scoreMap[a.account_id] = a.suspicion_score
  })

  report.fraud_rings.forEach((ring, i) => {
    const col = RING_COLORS[i % RING_COLORS.length]
    ring.member_accounts.forEach((acc) => {
      ringMap[acc] = { ring, col }
    })
    // mark every directed pair inside the ring
    for (let a = 0; a < ring.member_accounts.length; a++) {
      for (let b = 0; b < ring.member_accounts.length; b++) {
        if (a !== b) {
          ringEdgeMap[`${ring.member_accounts[a]}→${ring.member_accounts[b]}`] = col
        }
      }
    }
  })

  return { suspMap, scoreMap, ringMap, ringEdgeMap }
}

/** Build D3-compatible nodes and links arrays from raw transactions + lookups */
export function buildGraphData(transactions, { suspMap, scoreMap, ringMap }) {
  const nodeIds = new Set()
  transactions.forEach((t) => {
    nodeIds.add(t.sender_id)
    nodeIds.add(t.receiver_id)
  })

  const nodes = Array.from(nodeIds).map((id) => ({
    id,
    susp:  suspMap[id]  || null,
    ring:  ringMap[id]  || null,
    score: scoreMap[id] || 0,
  }))

  const links = transactions.map((t) => ({
    source:  t.sender_id,
    target:  t.receiver_id,
    amount:  t.amount,
    tx_id:   t.transaction_id,
    ts:      t.timestamp,
  }))

  return { nodes, links }
}
