import React, { useEffect, useRef, useState } from 'react';
import ForceGraph from 'react-force-graph-2d';
import '../styles/components.css';

function GraphVisualization({ data, onNodeClick, selectedAccount }) {
  const fgRef = useRef();
  const [hoveredNode, setHoveredNode] = useState(null);

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="no-data">
        <p>No graph data available</p>
      </div>
    );
  }

  const handleNodeClick = (node) => {
    onNodeClick(node.id);
  };

  const handleNodeHover = (node) => {
    setHoveredNode(node ? node.id : null);
  };

  // Create links from suspicious relationships
  const links = data.nodes
    .filter(n => n.isSuspicious || hoveredNode === n.id || selectedAccount === n.id)
    .flatMap((node, idx) => {
      // Create connections between suspicious nodes in same ring
      return data.nodes
        .filter((other, odx) => odx > idx && other.ringId === node.ringId && node.ringId)
        .map(other => ({
          source: node.id,
          target: other.id,
          ring: node.ringId,
        }));
    });

  const graphData = {
    nodes: data.nodes,
    links,
  };

  return (
    <div className="graph-visualization">
      <div className="graph-container">
        <ForceGraph
          ref={fgRef}
          graphData={graphData}
          nodeColor={(node) => {
            if (selectedAccount === node.id) return '#00ff00';
            if (hoveredNode === node.id) return '#ffff00';
            if (node.isSuspicious) {
              if (node.suspicionScore > 80) return '#e63946';
              if (node.suspicionScore > 50) return '#ffd60a';
              return '#ff006e';
            }
            return '#00d4ff';
          }}
          nodeRelSize={node => {
            if (node.isSuspicious) return 8;
            return 5;
          }}
          nodeCanvasObject={(node, ctx) => {
            const size =
              selectedAccount === node.id
                ? 12
                : hoveredNode === node.id
                ? 10
                : node.isSuspicious
                ? 8
                : 5;

            // Draw node
            ctx.fillStyle = node.isSuspicious
              ? node.suspicionScore > 80
                ? '#e63946'
                : node.suspicionScore > 50
                ? '#ffd60a'
                : '#ff006e'
              : '#00d4ff';
            ctx.beginPath();
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
            ctx.fill();

            // Draw border for suspicious/selected
            if (node.isSuspicious || selectedAccount === node.id || hoveredNode === node.id) {
              ctx.strokeStyle = selectedAccount === node.id ? '#00ff00' : 'rgba(255,255,255,0.3)';
              ctx.lineWidth = 2;
              ctx.stroke();
            }

            // Draw label
            const label = node.id;
            ctx.font = '12px Arial';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, node.x, node.y + size + 15);
          }}
          linkColor={() => 'rgba(0, 212, 255, 0.3)'}
          linkWidth={2}
          linkCanvasObject={(link, ctx) => {
            ctx.strokeStyle = link.ring ? 'rgba(255, 106, 106, 0.5)' : 'rgba(0, 212, 255, 0.3)';
            ctx.lineWidth = link.ring ? 2 : 1;
            ctx.beginPath();
            ctx.moveTo(link.source.x, link.source.y);
            ctx.lineTo(link.target.x, link.target.y);
            ctx.stroke();
          }}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          backgroundColor="rgba(15, 20, 25, 0.5)"
          enableNodeDrag={true}
          enablePanInteraction={true}
          enableZoomInteraction={true}
          width={window.innerWidth - 100}
          height={500}
        />
      </div>
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#00d4ff' }}></div>
          <span>Normal Account</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ff006e' }}></div>
          <span>Suspicious Account (Low-Medium)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ffd60a' }}></div>
          <span>Suspicious Account (Medium-High)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#e63946' }}></div>
          <span>Suspicious Account (Very High)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#00ff00' }}></div>
          <span>Selected Account</span>
        </div>
      </div>
    </div>
  );
}

export default GraphVisualization;
