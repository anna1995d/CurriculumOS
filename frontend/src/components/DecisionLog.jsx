const AUTONOMY_COLORS = {
  full:      'bg-blue-100 text-blue-700',
  draft:     'bg-purple-100 text-purple-700',
  recommend: 'bg-cyan-100 text-cyan-700',
  advisory:  'bg-orange-100 text-orange-700',
  escalate:  'bg-red-100 text-red-700',
}

function fmt(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function DecisionLog({ entries = [], brief, collapsed, onToggle }) {
  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-gray-200 shrink-0">
        {!collapsed && <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex-1">Decision Log</p>}
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-gray-700 text-base font-bold leading-none px-1 ml-auto"
          title={collapsed ? 'Expand log' : 'Collapse log'}
        >
          {collapsed ? '»' : '«'}
        </button>
      </div>

      {!collapsed && (
        <>
          {brief && (
            <div className="p-3 border-b border-gray-100 shrink-0">
              <p className="text-xs font-semibold text-gray-800 leading-tight">{brief.title}</p>
              <p className="text-xs text-gray-400 mt-0.5">{brief.topic_area} · {brief.duration}</p>
            </div>
          )}
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5 bg-gray-50">
            {entries.length === 0 && (
              <p className="text-xs text-gray-400 mt-3 text-center">No decisions yet.</p>
            )}
            {entries.map((e) => (
              <div
                key={e.id}
                className={`rounded-lg p-2.5 text-xs border ${e.human_override ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-100'}`}
              >
                <div className="flex items-center gap-1 mb-1 flex-wrap">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${AUTONOMY_COLORS[e.autonomy_level] || 'bg-gray-100 text-gray-500'}`}>
                    {e.autonomy_level}
                  </span>
                  {e.human_override && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-700 font-semibold">human</span>
                  )}
                  <span className="ml-auto text-gray-400 font-mono text-[10px]">{fmt(e.timestamp)}</span>
                </div>
                <p className="text-gray-700 font-medium">{e.node_id.replace('node-', '')}</p>
                <p className="text-gray-500 mt-0.5 leading-relaxed">{e.action}</p>
                {e.human_decision && (
                  <p className="text-amber-600 mt-0.5 font-medium">→ {e.human_decision}</p>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
