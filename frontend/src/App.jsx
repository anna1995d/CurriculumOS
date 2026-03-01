import { useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import BriefWizard from './components/BriefWizard'
import ChatPanel from './components/ChatPanel'
import DecisionLog from './components/DecisionLog'
import NodeDetail from './components/NodeDetail'
import PipelineGraph from './components/PipelineGraph'
import ResultsView from './components/ResultsView'
import { usePipeline } from './hooks/usePipeline'

const STATUS_BADGE = {
  created:   'bg-slate-100 text-slate-600',
  running:   'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  failed:    'bg-red-100 text-red-700',
}

export default function App() {
  const {
    pipelineId, pipeline, logEntries, connected, error,
    submitBrief, startPipeline, approveNode, editNode, decideNode, sendChat,
  } = usePipeline()

  const [selectedNode, setSelectedNode] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [activeTab, setActiveTab] = useState('graph') // 'graph' | 'results'
  const [logCollapsed, setLogCollapsed] = useState(false)
  const [rightExpanded, setRightExpanded] = useState(false)

  const view = pipeline?.status && pipeline.status !== 'created' ? 'pipeline'
    : pipelineId ? 'ready'
    : 'brief'

  async function handleSubmit(brief) {
    setSubmitting(true)
    try {
      await submitBrief(brief)
    } catch (e) {
      alert('Failed to submit brief: ' + e.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleStart() {
    try {
      await startPipeline()
    } catch (e) {
      alert('Failed to start pipeline: ' + e.message)
    }
  }

  // Keep selected node in sync with live pipeline state
  const liveSelectedNode = selectedNode
    ? pipeline?.nodes?.find(n => n.id === selectedNode.id) || selectedNode
    : null

  const awaitingCount = pipeline?.nodes?.filter(n => n.status === 'awaiting_human').length || 0

  const showExpanded = rightExpanded

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-slate-50">
      {/* Brief wizard / ready screen */}
      {(view === 'brief' || view === 'ready') && (
        <BriefWizard
          onSubmit={handleSubmit}
          onStart={handleStart}
          pipelineId={pipelineId}
          submitting={submitting}
        />
      )}

      {/* Pipeline view */}
      {view === 'pipeline' && (
        <>
          {/* Top bar */}
          <div className="flex items-center gap-4 px-4 py-2 border-b border-slate-200 bg-white shrink-0">
            <span className="text-sm font-bold text-slate-800">CurriculumOS</span>
            <span className="text-slate-300">|</span>
            <span className="text-sm text-slate-500 truncate max-w-xs">{pipeline?.brief?.title}</span>

            {/* View tabs */}
            <div className="flex border border-slate-200 rounded-lg overflow-hidden ml-4">
              {[['graph', 'Pipeline'], ['results', 'Results']].map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`px-3 py-1 text-xs font-semibold transition-colors ${
                    activeTab === id ? 'bg-slate-800 text-white' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 ml-auto">
              {awaitingCount > 0 && (
                <button
                  onClick={() => setActiveTab('graph')}
                  className="px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-700 font-semibold border border-amber-200 animate-pulse"
                >
                  {awaitingCount} awaiting your input
                </button>
              )}
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${STATUS_BADGE[pipeline?.status] || 'bg-slate-100 text-slate-500'}`}>
                {pipeline?.status}
              </span>
              <div
                className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-slate-300'}`}
                title={connected ? 'Live' : 'Disconnected'}
              />
            </div>
          </div>

          {/* Error banner */}
          {error && (
            <div className="px-4 py-2 bg-red-50 border-b border-red-200 text-xs text-red-700 shrink-0">
              Pipeline error: {error}
            </div>
          )}

          {/* Results tab */}
          {activeTab === 'results' && (
            <div className="flex flex-1 overflow-hidden">
              <ResultsView pipeline={pipeline} />
            </div>
          )}

          {/* Graph tab — 3-panel layout */}
          {activeTab === 'graph' && (
            <div className="flex flex-1 overflow-hidden">
              {/* Left: decision log (collapsible) */}
              <div className={`${logCollapsed ? 'w-10' : 'w-72'} border-r border-slate-200 bg-white flex flex-col overflow-hidden shrink-0 transition-all duration-200`}>
                <DecisionLog
                  entries={logEntries}
                  brief={pipeline?.brief}
                  collapsed={logCollapsed}
                  onToggle={() => setLogCollapsed(v => !v)}
                />
              </div>

              {/* Center: graph */}
              <div className="flex-1 overflow-hidden min-w-0">
                <ReactFlowProvider>
                  <PipelineGraph
                    nodes={pipeline?.nodes || []}
                    selectedNodeId={liveSelectedNode?.id}
                    onNodeClick={(node) => {
                      setSelectedNode(node)
                      setChatOpen(false)
                      // Auto-expand panel for conflict nodes awaiting human input
                      if (node.type === 'conflict' && node.status === 'awaiting_human') {
                        setRightExpanded(true)
                      }
                    }}
                  />
                </ReactFlowProvider>
              </div>

              {/* Right: node detail (expandable) */}
              <div
                className={`${showExpanded ? 'w-2/3' : 'w-96'} border-l border-slate-200 bg-white flex flex-col overflow-hidden shrink-0 transition-all duration-200`}
                style={showExpanded ? { maxWidth: '66%' } : {}}
              >
                {/* Panel header with expand toggle */}
                <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-100 bg-slate-50 shrink-0">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wide flex-1">
                    {liveSelectedNode ? liveSelectedNode.label : 'Node Inspector'}
                  </span>
                  {liveSelectedNode && (
                    <button
                      onClick={() => setRightExpanded(v => !v)}
                      title={showExpanded ? 'Collapse panel' : 'Expand panel'}
                      className="text-[10px] text-slate-400 hover:text-slate-700 px-1 py-0.5 rounded hover:bg-slate-200 transition-colors"
                    >
                      {showExpanded ? '→' : '←'}
                    </button>
                  )}
                </div>
                <div className="flex-1 overflow-hidden">
                  <NodeDetail
                    node={liveSelectedNode}
                    onApprove={approveNode}
                    onEdit={editNode}
                    onDecide={decideNode}
                    onChat={() => setChatOpen(true)}
                  />
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Chat panel */}
      {chatOpen && liveSelectedNode && (
        <ChatPanel
          node={liveSelectedNode}
          onClose={() => setChatOpen(false)}
          onSendChat={sendChat}
        />
      )}
    </div>
  )
}
