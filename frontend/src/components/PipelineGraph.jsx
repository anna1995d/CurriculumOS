import { useCallback, useEffect } from 'react'
import {
  Background, Controls, Handle, Position,
  ReactFlow, useEdgesState, useNodesState, useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { layoutNodes } from '../utils/graphLayout'

const STATUS_STYLES = {
  pending:        { bg: '#f1f5f9', border: '#cbd5e1', text: '#475569', pulse: false },
  running:        { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af', pulse: true  },
  completed:      { bg: '#dcfce7', border: '#16a34a', text: '#15803d', pulse: false },
  awaiting_human: { bg: '#fef3c7', border: '#d97706', text: '#78350f', pulse: true  },
  blocked:        { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', pulse: false },
  error:          { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', pulse: false },
}

const TYPE_ICONS = {
  orchestrator:'⚙', research:'🔬', audience:'👥', catalog:'📚', outline:'📋',
  script:'✍', review_technical:'🔧', review_pedagogy:'🎓', review_business:'💼', conflict:'⚖',
}

function PipelineNode({ data, selected }) {
  const s = STATUS_STYLES[data.status] || STATUS_STYLES.pending
  return (
    <div style={{
      background: s.bg, border: `2px solid ${s.border}`, borderRadius: 10,
      width: 200, padding: '8px 12px',
      boxShadow: selected ? `0 0 0 3px ${s.border}55, 0 2px 8px rgba(0,0,0,0.1)` : '0 1px 4px rgba(0,0,0,0.08)',
      animation: s.pulse ? 'pulse-ring 1.5s ease-in-out infinite' : 'none',
      transition: 'box-shadow 0.15s',
    }}>
      <Handle type="target" position={Position.Top}
        style={{ background: '#94a3b8', border: 'none', width: 8, height: 8 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <span style={{ fontSize: 13 }}>{TYPE_ICONS[data.type] || '●'}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: s.text, lineHeight: 1.2 }} className="truncate">
          {data.label}
        </span>
      </div>
      <div style={{ fontSize: 9, color: s.text, opacity: 0.7, textTransform: 'uppercase', letterSpacing: 1 }}>
        {data.status?.replace('_', ' ')}
      </div>
      <Handle type="source" position={Position.Bottom}
        style={{ background: '#94a3b8', border: 'none', width: 8, height: 8 }} />
    </div>
  )
}

const nodeTypes = { pipelineNode: PipelineNode }

function AutoFit({ trigger }) {
  const { fitView } = useReactFlow()
  useEffect(() => {
    setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 100)
  }, [trigger, fitView])
  return null
}

export default function PipelineGraph({ nodes: pipelineNodes = [], selectedNodeId, onNodeClick }) {
  const { rfNodes, rfEdges } = layoutNodes(pipelineNodes)
  const [nodes, setNodes, onNodesChange] = useNodesState(rfNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(rfEdges)

  useEffect(() => {
    const { rfNodes: newNodes, rfEdges: newEdges } = layoutNodes(pipelineNodes)
    setNodes(newNodes.map(n => ({ ...n, selected: n.id === selectedNodeId })))
    setEdges(newEdges)
  }, [pipelineNodes, selectedNodeId, setNodes, setEdges])

  const handleNodeClick = useCallback((_, node) => onNodeClick(node.data), [onNodeClick])

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView minZoom={0.2} maxZoom={2}
        style={{ background: '#f8fafc' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#e2e8f0" gap={20} />
        <Controls style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8 }} />
        <AutoFit trigger={pipelineNodes.length} />
      </ReactFlow>
    </div>
  )
}
