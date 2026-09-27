import React, { useMemo } from 'react';
import { Workflow } from 'lucide-react';

export const MermaidDiagram = ({ chart }) => {
  const parsedData = useMemo(() => {
    if (!chart) return null;
    try {
      const clean = chart.replace(/```mermaid/gi, '').replace(/```/g, '').trim();
      const lines = clean.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('flowchart') && !l.startsWith('graph'));

      const nodesMap = new Map();
      const edges = [];

      const getOrCreateNode = (rawId, rawLabel) => {
        const id = rawId.trim();
        let label = (rawLabel || id).trim().replace(/^["']|["']$/g, '');
        if (!nodesMap.has(id)) {
          nodesMap.set(id, { id, label });
        } else if (rawLabel && nodesMap.get(id).label === id) {
          nodesMap.get(id).label = label;
        }
        return id;
      };

      lines.forEach(line => {
        const edgeMatch = line.match(/^([A-Za-z0-9_]+)(?:\[([^\]]+)\])?\s*(?:-->(?:\|([^|]+)\|)?|-->)\s*([A-Za-z0-9_]+)(?:\[([^\]]+)\])?/);
        if (edgeMatch) {
          const [, fromId, fromLabel, edgeText, toId, toLabel] = edgeMatch;
          const u = getOrCreateNode(fromId, fromLabel);
          const v = getOrCreateNode(toId, toLabel);
          edges.push({ from: u, to: v, label: edgeText || '' });
        } else {
          const singleMatch = line.match(/^([A-Za-z0-9_]+)\[([^\]]+)\]/);
          if (singleMatch) {
            getOrCreateNode(singleMatch[1], singleMatch[2]);
          }
        }
      });

      const nodes = Array.from(nodesMap.values());
      if (nodes.length === 0) return null;
      return { raw: clean, nodes, edges };
    } catch (e) {
      return null;
    }
  }, [chart]);

  if (!parsedData || parsedData.nodes.length === 0) {
    const raw = chart ? chart.replace(/```mermaid/gi, '').replace(/```/g, '').trim() : '';
    return (
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl text-xs text-slate-300 font-mono overflow-x-auto">
        <div className="text-amber-400 font-semibold mb-2 flex items-center gap-2">
          <Workflow className="w-4 h-4" /> Educational Process Logic
        </div>
        <pre className="text-slate-300 whitespace-pre-wrap">{raw}</pre>
      </div>
    );
  }

  const { nodes, edges, raw } = parsedData;
  const isHorizontal = raw.includes('flowchart LR') || raw.includes('graph LR');

  const nodeWidth = 140;
  const nodeHeight = 44;
  const gapX = isHorizontal ? 70 : 40;
  const gapY = isHorizontal ? 40 : 60;

  const levels = new Map();
  nodes.forEach(n => levels.set(n.id, 0));

  edges.forEach(({ from, to }) => {
    const fromLvl = levels.get(from) || 0;
    const currentToLvl = levels.get(to) || 0;
    levels.set(to, Math.max(currentToLvl, fromLvl + 1));
  });

  const levelGroups = new Map();
  nodes.forEach(n => {
    const lvl = levels.get(n.id) || 0;
    if (!levelGroups.has(lvl)) levelGroups.set(lvl, []);
    levelGroups.get(lvl).push(n);
  });

  const maxPerLvl = Math.max(...Array.from(levelGroups.values()).map(g => g.length), 1);
  const totalLevels = Math.max(...Array.from(levelGroups.keys()), 0) + 1;

  const positions = new Map();

  levelGroups.forEach((groupNodes, lvl) => {
    groupNodes.forEach((n, idx) => {
      let x, y;
      if (isHorizontal) {
        x = 40 + lvl * (nodeWidth + gapX);
        const startY = 40 + (maxPerLvl - groupNodes.length) * (nodeHeight + gapY) / 2;
        y = startY + idx * (nodeHeight + gapY);
      } else {
        const startX = 40 + (maxPerLvl - groupNodes.length) * (nodeWidth + gapX) / 2;
        x = startX + idx * (nodeWidth + gapX);
        y = 40 + lvl * (nodeHeight + gapY);
      }
      positions.set(n.id, { x, y });
    });
  });

  const svgWidth = isHorizontal 
    ? 80 + totalLevels * (nodeWidth + gapX) 
    : 80 + maxPerLvl * (nodeWidth + gapX);
  const svgHeight = isHorizontal 
    ? 80 + maxPerLvl * (nodeHeight + gapY) 
    : 80 + totalLevels * (nodeHeight + gapY);

  return (
    <div className="w-full bg-slate-900/95 border border-slate-800 rounded-2xl p-4 overflow-x-auto flex flex-col items-center space-y-3">
      <div className="w-full flex items-center justify-between text-xs text-slate-400 border-b border-slate-800/80 pb-2">
        <span className="font-semibold text-blue-400 flex items-center gap-2">
          <Workflow className="w-4 h-4 text-blue-400" />
          Interactive Educational Flowchart
        </span>
        <span className="text-[10px] bg-blue-500/10 text-blue-300 border border-blue-500/20 px-2 py-0.5 rounded-full font-mono">
          Visual Diagram
        </span>
      </div>

      <svg width={svgWidth} height={svgHeight} className="mx-auto block">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#60a5fa" />
          </marker>
          <linearGradient id="nodeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>
        </defs>

        {/* Draw Edges */}
        {edges.map(({ from, to, label }, i) => {
          const p1 = positions.get(from);
          const p2 = positions.get(to);
          if (!p1 || !p2) return null;

          const startX = p1.x + nodeWidth / 2;
          const startY = p1.y + nodeHeight / 2;
          const endX = p2.x + nodeWidth / 2;
          const endY = p2.y + nodeHeight / 2;

          return (
            <g key={`edge-${i}`}>
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                stroke="#475569"
                strokeWidth="2"
                markerEnd="url(#arrow)"
              />
              {label && (
                <text
                  x={(startX + endX) / 2}
                  y={(startY + endY) / 2 - 6}
                  fill="#94a3b8"
                  fontSize="10"
                  fontFamily="sans-serif"
                  textAnchor="middle"
                >
                  {label}
                </text>
              )}
            </g>
          );
        })}

        {/* Draw Nodes */}
        {nodes.map(n => {
          const pos = positions.get(n.id);
          if (!pos) return null;
          return (
            <g key={`node-${n.id}`} transform={`translate(${pos.x}, ${pos.y})`}>
              <rect
                width={nodeWidth}
                height={nodeHeight}
                rx="12"
                ry="12"
                fill="url(#nodeGradient)"
                stroke="#3b82f6"
                strokeWidth="1.5"
                className="drop-shadow-md"
              />
              <text
                x={nodeWidth / 2}
                y={nodeHeight / 2 + 4}
                fill="#f8fafc"
                fontSize="11"
                fontWeight="600"
                fontFamily="sans-serif"
                textAnchor="middle"
              >
                {n.label.length > 18 ? n.label.substring(0, 16) + '...' : n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default MermaidDiagram;
