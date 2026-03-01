// Results view: displays the full course output once a pipeline completes.
// Navigable by module — shows outline, scripts, review summaries, and conflict resolutions.

import { useState } from 'react'

const VERDICT_CLS = {
  approve: 'bg-green-100 text-green-700',
  flag:    'bg-amber-100 text-amber-700',
  reject:  'bg-red-100 text-red-700',
}

const SEV_CLS = {
  info:     'text-blue-600',
  warning:  'text-amber-600',
  critical: 'text-red-600',
}

function Badge({ children, cls = 'bg-slate-100 text-slate-600' }) {
  return <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${cls}`}>{children}</span>
}

export default function ResultsView({ pipeline }) {
  const nodes = pipeline?.nodes || []
  const brief = pipeline?.brief || {}

  const outline = nodes.find(n => n.type === 'outline')?.output_data
  const modules = outline?.modules || []

  // Build a map of module id → relevant nodes
  const moduleMap = {}
  for (const m of modules) {
    const mid = m.id
    moduleMap[mid] = {
      module: m,
      script:   nodes.find(n => n.id === `node-script-${mid}`),
      tech:     nodes.find(n => n.id === `node-review-tech-${mid}`),
      ped:      nodes.find(n => n.id === `node-review-ped-${mid}`),
      biz:      nodes.find(n => n.id === `node-review-biz-${mid}`),
      conflict: nodes.find(n => n.id === `node-conflict-${mid}`),
    }
  }

  const [selectedMid, setSelectedMid] = useState(modules[0]?.id || null)
  const [tab, setTab] = useState('script')

  const current = selectedMid ? moduleMap[selectedMid] : null

  function exportJSON() {
    const data = {
      title: brief.title,
      outline,
      modules: modules.map(m => ({
        ...m,
        script: moduleMap[m.id]?.script?.output_data,
        reviews: {
          technical: moduleMap[m.id]?.tech?.output_data,
          pedagogy:  moduleMap[m.id]?.ped?.output_data,
          business:  moduleMap[m.id]?.biz?.output_data,
        },
        conflict_resolution: moduleMap[m.id]?.conflict?.output_data,
      })),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${brief.title?.replace(/\s+/g, '_') || 'course'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (modules.length === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-50">
        <p className="text-slate-400 text-sm">
          {pipeline?.status === 'completed' ? 'No modules found in outline.' : 'Pipeline not yet complete.'}
        </p>
      </div>
    )
  }

  return (
    <div className="flex h-full overflow-hidden bg-slate-50">
      {/* Left sidebar — module list */}
      <div className="w-64 border-r border-slate-200 bg-white flex flex-col overflow-hidden shrink-0">
        <div className="p-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-slate-900 leading-tight">{brief.title}</h2>
          <p className="text-xs text-slate-500 mt-1">{brief.topic_area} · {brief.duration}</p>
          <p className="text-xs text-slate-400 mt-1">{modules.length} modules · {outline?.total_duration_minutes} min</p>
          <button
            onClick={exportJSON}
            className="mt-3 w-full py-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded text-xs text-slate-600 transition-colors"
          >
            ↓ Export JSON
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-2">
          {modules.map((m, i) => {
            const entry = moduleMap[m.id]
            const needsAction = entry?.conflict?.status === 'awaiting_human'

            return (
              <button
                key={m.id}
                onClick={() => { setSelectedMid(m.id); setTab('script') }}
                className={`w-full text-left rounded-lg p-2.5 mb-1 transition-colors ${
                  selectedMid === m.id
                    ? 'bg-blue-600 text-white'
                    : 'hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className={`text-[10px] font-mono ${selectedMid === m.id ? 'text-blue-200' : 'text-slate-400'}`}>{i + 1}</span>
                  {needsAction && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />}
                </div>
                <p className={`text-xs font-semibold leading-tight ${selectedMid === m.id ? 'text-white' : 'text-slate-800'}`}>{m.title}</p>
                <p className={`text-[10px] mt-0.5 ${selectedMid === m.id ? 'text-blue-200' : 'text-slate-400'}`}>{m.duration_minutes}min · {m.activity_type}</p>
              </button>
            )
          })}
        </div>

        {/* Course overview */}
        <div className="p-3 border-t border-slate-200">
          <p className="text-[10px] text-slate-400 uppercase mb-2">Overview</p>
          <div className="space-y-1 text-xs text-slate-500">
            <p>Audience: <span className="text-slate-700">{brief.audience}</span></p>
            <p>Format: <span className="text-slate-700">{brief.format}</span></p>
            <p>Balance: <span className="text-slate-700">{Math.round((brief.balance || 0) * 100)}% hands-on</span></p>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {current && (
          <>
            {/* Module header */}
            <div className="px-6 py-4 border-b border-slate-200 bg-white shrink-0">
              <h3 className="text-base font-bold text-slate-900">{current.module.title}</h3>
              <div className="flex gap-3 mt-1 text-xs text-slate-500">
                <span>{current.module.duration_minutes} min</span>
                <span>·</span>
                <span>{current.module.activity_type}</span>
                {current.module.prerequisite_concepts?.length > 0 && (
                  <>
                    <span>·</span>
                    <span>Prereqs: {current.module.prerequisite_concepts.join(', ')}</span>
                  </>
                )}
              </div>
              {current.module.learning_objectives?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {current.module.learning_objectives.map((obj, i) => (
                    <span key={i} className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] text-slate-600">{obj}</span>
                  ))}
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200 bg-white shrink-0">
              {[
                ['script',   'Script',          current.script],
                ['reviews',  'Reviews',         current.tech || current.ped || current.biz],
                ['conflict', 'Conflict Report', current.conflict],
              ].map(([id, label, node]) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={`px-4 py-2.5 text-xs font-semibold transition-colors border-b-2 ${
                    tab === id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {label}
                  {node?.status === 'awaiting_human' && (
                    <span className="ml-1.5 w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
                  )}
                  {!node && <span className="ml-1.5 text-slate-300">—</span>}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
              {tab === 'script'   && <ScriptTab node={current.script} />}
              {tab === 'reviews'  && <ReviewsTab tech={current.tech} ped={current.ped} biz={current.biz} />}
              {tab === 'conflict' && <ConflictTab node={current.conflict} />}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function ScriptTab({ node }) {
  if (!node) return <Placeholder text="Script not yet generated." />
  if (node.status === 'running') return <Placeholder text="Generating script…" spinner />
  const out = node.output_data || {}
  const sections = out.sections || []

  return (
    <div className="max-w-3xl space-y-6">
      {out.transition_in && (
        <div className="bg-white border border-slate-200 rounded-lg p-3 border-l-4 border-l-blue-400">
          <p className="text-[10px] text-blue-600 uppercase mb-1">Transition In</p>
          <p className="text-xs text-slate-700">{out.transition_in}</p>
        </div>
      )}

      {sections.map((s, i) => (
        <div key={i} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-bold text-slate-900">{s.title}</h4>
            <span className="text-xs text-slate-400">{s.duration_minutes} min</span>
          </div>

          <p className="text-sm text-slate-700 leading-relaxed mb-4 whitespace-pre-wrap">{s.speaker_notes}</p>

          {s.key_points?.length > 0 && (
            <div className="mb-3">
              <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1.5">Key Points</p>
              <ul className="space-y-1">
                {s.key_points.map((kp, j) => (
                  <li key={j} className="text-xs text-slate-700 flex gap-2">
                    <span className="text-blue-500 shrink-0">•</span>{kp}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {s.examples?.length > 0 && (
            <div className="mb-3 space-y-2">
              <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1.5">Examples</p>
              {s.examples.map((ex, j) => (
                <div key={j} className="bg-slate-50 border border-slate-200 rounded p-2.5">
                  <Badge cls="bg-slate-200 text-slate-600">{ex.type}</Badge>
                  <p className="text-xs text-slate-700 mt-1.5">{ex.content}</p>
                </div>
              ))}
            </div>
          )}

          {s.activity && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-[10px] text-blue-600 uppercase font-semibold">Activity</p>
                <Badge cls="bg-blue-100 text-blue-700">{s.activity.type}</Badge>
                <span className="text-[10px] text-slate-400 ml-auto">{s.activity.duration_minutes} min</span>
              </div>
              <p className="text-xs text-blue-800">{s.activity.description}</p>
            </div>
          )}
        </div>
      ))}

      {out.transition_out && (
        <div className="bg-white border border-slate-200 rounded-lg p-3 border-l-4 border-l-blue-400">
          <p className="text-[10px] text-blue-600 uppercase mb-1">Transition Out</p>
          <p className="text-xs text-slate-700">{out.transition_out}</p>
        </div>
      )}

      {out.materials_needed?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-lg p-3">
          <p className="text-[10px] text-slate-400 uppercase mb-2">Materials Needed</p>
          <div className="flex flex-wrap gap-1.5">
            {out.materials_needed.map((m, i) => (
              <span key={i} className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs text-slate-700">{m}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ReviewsTab({ tech, ped, biz }) {
  if (!tech && !ped && !biz) return <Placeholder text="Reviews not yet generated." />

  return (
    <div className="grid grid-cols-3 gap-4 max-w-5xl">
      {[
        ['Technical', tech],
        ['Pedagogy',  ped],
        ['Business',  biz],
      ].map(([label, node]) => (
        <div key={label} className="space-y-3">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-slate-800">{label}</h4>
            {node && <Badge cls={VERDICT_CLS[node.output_data?.verdict]}>{node.output_data?.verdict}</Badge>}
          </div>

          {!node && <p className="text-xs text-slate-400">Not yet run.</p>}
          {node?.status === 'running' && <p className="text-xs text-slate-500 animate-pulse">Reviewing…</p>}

          {node?.output_data && (
            <>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Confidence:</span>
                <div className="flex-1 bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-blue-500 h-1.5 rounded-full"
                    style={{ width: `${(node.output_data.confidence || 0) * 100}%` }}
                  />
                </div>
                <span className="text-slate-500">{Math.round((node.output_data.confidence || 0) * 100)}%</span>
              </div>

              <p className="text-xs text-slate-700 leading-relaxed">{node.output_data.reasoning}</p>

              {(node.output_data.findings || []).map((f, i) => (
                <div key={i} className="bg-white border border-slate-200 rounded p-2.5 text-xs">
                  <p>
                    <span className={`font-bold ${SEV_CLS[f.severity] || 'text-slate-500'}`}>[{f.severity}]</span>
                    {' '}<span className="text-slate-400 text-[10px]">{f.category}</span>
                  </p>
                  <p className="text-slate-700 mt-1">{f.description}</p>
                  <p className="text-slate-500 mt-1">→ {f.suggestion}</p>
                </div>
              ))}

              {(node.output_data.findings || []).length === 0 && (
                <p className="text-xs text-green-600">No issues found.</p>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  )
}

function ConflictTab({ node }) {
  if (!node) return <Placeholder text="Conflict resolution not yet run." />
  if (node.status === 'running') return <Placeholder text="Analysing conflicts…" spinner />

  const out = node.output_data || {}

  return (
    <div className="max-w-3xl space-y-6">
      {out.summary && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-[10px] text-slate-400 uppercase mb-2">Summary</p>
          <p className="text-sm text-slate-700 leading-relaxed">{out.summary}</p>
        </div>
      )}

      <div className="flex gap-4">
        {['technical', 'pedagogy', 'business'].map(r => (
          <div key={r} className="flex items-center gap-2">
            <span className="text-xs text-slate-500 capitalize">{r}:</span>
            <Badge cls={VERDICT_CLS[out.overall_verdicts?.[r]]}>{out.overall_verdicts?.[r] || '—'}</Badge>
          </div>
        ))}
      </div>

      {(out.agreements || []).length > 0 && (
        <div>
          <h4 className="text-sm font-bold text-slate-800 mb-3">
            ✓ Agreements ({out.agreements.length})
          </h4>
          <div className="space-y-2">
            {out.agreements.map((a, i) => (
              <div key={i} className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-green-700">{a.topic}</p>
                <p className="text-xs text-green-600 mt-1">{a.shared_recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {(out.disagreements || []).length > 0 && (
        <div>
          <h4 className="text-sm font-bold text-slate-800 mb-3">
            ⚖ Disagreements ({out.disagreements.length})
          </h4>
          <div className="space-y-4">
            {out.disagreements.map((d, i) => (
              <div key={i} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <h5 className="text-sm font-semibold text-slate-900">{d.topic}</h5>
                  <Badge cls={
                    d.conflict_type === 'factual'   ? 'bg-blue-100 text-blue-700' :
                    d.conflict_type === 'priority'  ? 'bg-orange-100 text-orange-700' :
                    'bg-purple-100 text-purple-700'
                  }>{d.conflict_type}</Badge>
                </div>

                <div className="grid grid-cols-3 gap-2 mb-3">
                  {Object.entries(d.positions || {}).map(([reviewer, pos]) => (
                    <div key={reviewer} className="bg-slate-50 border border-slate-200 rounded p-2">
                      <p className="text-[10px] text-slate-400 uppercase mb-1">{reviewer}</p>
                      <p className="text-xs text-slate-700">{pos}</p>
                    </div>
                  ))}
                </div>

                {d.ai_resolution && (
                  <div className="bg-blue-50 border border-blue-200 rounded p-2 mb-2">
                    <p className="text-[10px] text-blue-600 uppercase mb-1">AI Resolved</p>
                    <p className="text-xs text-blue-800">{d.ai_resolution}</p>
                  </div>
                )}

                {d.ai_assessment && !d.ai_resolution && (
                  <div className="bg-slate-50 border border-slate-200 rounded p-2 mb-2">
                    <p className="text-[10px] text-slate-400 uppercase mb-1">Why the AI didn't decide</p>
                    <p className="text-xs text-slate-600">{d.ai_assessment}</p>
                  </div>
                )}

                {(out.human_decisions || out.human_decision) && (
                  <div className="bg-amber-50 border border-amber-200 rounded p-2">
                    <p className="text-[10px] text-amber-600 uppercase mb-1">Human Decision</p>
                    <p className="text-xs text-amber-800">
                      {out.human_decisions?.[d.topic] || out.human_decision}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Placeholder({ text, spinner }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-400 mt-8">
      {spinner && <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-400 rounded-full animate-spin" />}
      {text}
    </div>
  )
}
