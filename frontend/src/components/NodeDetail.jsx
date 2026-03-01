import { useEffect, useState } from 'react'
import ConflictCard from './ConflictCard'
import ReviewPanel from './ReviewPanel'

const STATUS_META = {
  pending:        { label: 'Pending',        cls: 'bg-slate-100 text-slate-600' },
  running:        { label: 'Running',        cls: 'bg-blue-100 text-blue-700' },
  completed:      { label: 'Completed',      cls: 'bg-green-100 text-green-700' },
  awaiting_human: { label: 'Awaiting You',   cls: 'bg-amber-100 text-amber-700' },
  blocked:        { label: 'Blocked',        cls: 'bg-red-100 text-red-700' },
  error:          { label: 'Error',          cls: 'bg-red-100 text-red-700' },
}

const AUTONOMY_CLS = {
  full:      'bg-blue-100 text-blue-700',
  draft:     'bg-purple-100 text-purple-700',
  recommend: 'bg-cyan-100 text-cyan-700',
  advisory:  'bg-orange-100 text-orange-700',
  escalate:  'bg-red-100 text-red-700',
}

const AUTONOMY_DESC = {
  full:      'Acts autonomously — auditable after the fact',
  draft:     'Produces a draft — your approval required',
  recommend: 'Recommends — please confirm before use downstream',
  advisory:  'Flags issues — cannot modify output',
  escalate:  'Surfaces options — you make the final call',
}

function Section({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden mb-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left flex items-center justify-between px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100"
      >
        {title}
        <span className="text-slate-400 text-[10px]">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="px-3 pb-3 pt-2 bg-white">{children}</div>}
    </div>
  )
}

function JsonBlock({ data }) {
  return (
    <pre className="text-[10px] text-slate-600 bg-slate-50 border border-slate-200 rounded p-2 overflow-auto max-h-56 leading-relaxed whitespace-pre-wrap">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

// ── Audience Action UI ─────────────────────────────────────────────────────────

function AudienceActions({ node, onApprove, onEdit }) {
  const profile = node.output_data || {}
  const [form, setForm] = useState({
    profile_summary: '',
    assumed_knowledge: '',
    pain_points: '',
    knowledge_gaps: '',
  })

  useEffect(() => {
    const p = node.output_data || {}
    setForm({
      profile_summary: p.profile_summary || '',
      assumed_knowledge: (p.assumed_knowledge || []).join('\n'),
      pain_points: (p.pain_points || []).join('\n'),
      knowledge_gaps: (p.knowledge_gaps || []).join('\n'),
    })
  }, [node.output_data])

  function handleEdit() {
    onEdit({
      ...profile,
      profile_summary: form.profile_summary,
      assumed_knowledge: form.assumed_knowledge.split('\n').filter(Boolean),
      pain_points: form.pain_points.split('\n').filter(Boolean),
      knowledge_gaps: form.knowledge_gaps.split('\n').filter(Boolean),
    })
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 leading-relaxed">
        Does this profile match your audience? Edit any fields, then confirm.
      </p>

      {profile.red_flags?.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded p-2">
          <p className="text-[10px] text-red-600 uppercase mb-1">Agent Flags</p>
          {profile.red_flags.map((f, i) => <p key={i} className="text-xs text-red-700">{f}</p>)}
        </div>
      )}

      {[
        ['profile_summary', 'Profile Summary', 3],
        ['assumed_knowledge', 'Assumed Knowledge (one per line)', 3],
        ['pain_points', 'Pain Points (one per line)', 3],
        ['knowledge_gaps', 'Knowledge Gaps (one per line)', 2],
      ].map(([key, label, rows]) => (
        <div key={key}>
          <label className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</label>
          <textarea
            value={form[key]}
            onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
            rows={rows}
            className="w-full mt-1 bg-white border border-slate-300 rounded px-2 py-1.5 text-xs text-slate-800 resize-none outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"
          />
        </div>
      ))}

      {profile.engagement_strategies?.length > 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded p-2">
          <p className="text-[10px] text-slate-400 uppercase mb-1">Suggested Strategies</p>
          {profile.engagement_strategies.map((s, i) => (
            <p key={i} className="text-xs text-slate-600">• {s}</p>
          ))}
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button onClick={handleEdit} className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-xs font-semibold text-white transition-colors">
          Edit & Confirm
        </button>
        <button onClick={onApprove} className="flex-1 py-2 bg-green-600 hover:bg-green-700 rounded text-xs font-semibold text-white transition-colors">
          Looks Good ✓
        </button>
      </div>
    </div>
  )
}

// ── Catalog Action UI ──────────────────────────────────────────────────────────

function CatalogActions({ node, onApprove }) {
  const out = node.output_data || {}
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-amber-600">{out.max_overlap_score}%</span>
        <div>
          <p className="text-xs font-semibold text-slate-800">Catalog overlap detected</p>
          <p className="text-[10px] text-slate-500">Pipeline is paused until you decide</p>
        </div>
      </div>
      <p className="text-xs text-slate-700 leading-relaxed bg-amber-50 border border-amber-200 rounded p-2">{out.recommendation}</p>
      {(out.overlap_analysis || []).filter(o => o.overlap_score > 0).map(o => (
        <div key={o.course_id} className="bg-white border border-slate-200 rounded p-2 text-xs">
          <div className="flex items-center justify-between mb-1">
            <p className="font-semibold text-slate-800">{o.course_title}</p>
            <span className="text-amber-600 font-bold">{o.overlap_score}%</span>
          </div>
          <p className="text-slate-500">{o.overlap_reason}</p>
          {o.overlapping_topics?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {o.overlapping_topics.map((t, i) => (
                <span key={i} className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] text-slate-600">{t}</span>
              ))}
            </div>
          )}
        </div>
      ))}
      {(out.reusable_modules || []).length > 0 && (
        <div>
          <p className="text-[10px] text-slate-400 uppercase mb-1">Reuse Opportunities</p>
          {out.reusable_modules.map((m, i) => (
            <div key={i} className="bg-green-50 border border-green-200 rounded p-2 mb-1 text-xs">
              <p className="font-semibold text-green-700">{m.module_title}</p>
              <p className="text-green-600">{m.reuse_suggestion}</p>
            </div>
          ))}
        </div>
      )}
      <button onClick={onApprove} className="w-full py-2.5 bg-amber-500 hover:bg-amber-600 rounded text-xs font-semibold text-white transition-colors">
        Proceed Anyway — Differentiate from Existing Courses
      </button>
    </div>
  )
}

// ── Outline Action UI ──────────────────────────────────────────────────────────

const ACTIVITY_TYPES = ['lecture', 'workshop', 'lab', 'discussion', 'case-study', 'demo', 'quiz', 'project']

function ModuleEditor({ module, index, onChange, onRemove, onMove, total }) {
  const [open, setOpen] = useState(false)
  const m = module

  function updateField(key, value) {
    onChange({ ...m, [key]: value })
  }

  function updateObjective(i, val) {
    const objs = [...(m.learning_objectives || [])]
    objs[i] = val
    onChange({ ...m, learning_objectives: objs })
  }

  function addObjective() {
    onChange({ ...m, learning_objectives: [...(m.learning_objectives || []), ''] })
  }

  function removeObjective(i) {
    onChange({ ...m, learning_objectives: (m.learning_objectives || []).filter((_, idx) => idx !== i) })
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      {/* Summary row */}
      <div className="flex items-center gap-2 bg-white px-2.5 py-2 group">
        <div className="flex flex-col gap-0.5 shrink-0">
          <button onClick={() => onMove(index, -1)} disabled={index === 0} className="text-[10px] text-slate-400 hover:text-slate-700 disabled:opacity-30 leading-none">▲</button>
          <button onClick={() => onMove(index, 1)} disabled={index === total - 1} className="text-[10px] text-slate-400 hover:text-slate-700 disabled:opacity-30 leading-none">▼</button>
        </div>
        <span className="text-[10px] text-slate-400 font-mono w-4 shrink-0">{index + 1}</span>
        <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setOpen(o => !o)}>
          <p className="text-xs font-semibold text-slate-800 truncate">{m.title || <span className="text-slate-400 italic">Untitled</span>}</p>
          <div className="flex gap-2 text-[10px] text-slate-400 mt-0.5">
            <span>{m.duration_minutes || 0}min</span>
            <span>·</span>
            <span>{m.activity_type || '—'}</span>
          </div>
        </div>
        <button onClick={() => setOpen(o => !o)} className="text-[10px] text-slate-400 hover:text-slate-700 px-1">
          {open ? '▲' : '▼'}
        </button>
        <button onClick={() => onRemove(index)} className="text-[10px] text-red-400 hover:text-red-600 px-1">✕</button>
      </div>

      {/* Edit form */}
      {open && (
        <div className="px-3 pb-3 pt-2 bg-slate-50 border-t border-slate-200 space-y-2.5">
          <div>
            <label className="text-[10px] text-slate-500 uppercase">Title</label>
            <input
              value={m.title || ''}
              onChange={e => updateField('title', e.target.value)}
              className="w-full mt-0.5 bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 outline-none focus:border-blue-400"
              placeholder="Module title"
            />
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <label className="text-[10px] text-slate-500 uppercase">Duration (min)</label>
              <input
                type="number"
                value={m.duration_minutes || ''}
                onChange={e => updateField('duration_minutes', parseInt(e.target.value) || 0)}
                className="w-full mt-0.5 bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 outline-none focus:border-blue-400"
              />
            </div>
            <div className="flex-1">
              <label className="text-[10px] text-slate-500 uppercase">Activity Type</label>
              <select
                value={m.activity_type || ''}
                onChange={e => updateField('activity_type', e.target.value)}
                className="w-full mt-0.5 bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 outline-none focus:border-blue-400"
              >
                <option value="">Select…</option>
                {ACTIVITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label className="text-[10px] text-slate-500 uppercase">Learning Objectives</label>
              <button onClick={addObjective} className="text-[10px] text-blue-600 hover:text-blue-800">+ Add</button>
            </div>
            <div className="mt-0.5 space-y-1">
              {(m.learning_objectives || []).map((obj, i) => (
                <div key={i} className="flex gap-1">
                  <input
                    value={obj}
                    onChange={e => updateObjective(i, e.target.value)}
                    className="flex-1 bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 outline-none focus:border-blue-400"
                    placeholder={`Objective ${i + 1}`}
                  />
                  <button onClick={() => removeObjective(i)} className="text-[10px] text-red-400 hover:text-red-600 px-1">✕</button>
                </div>
              ))}
              {(m.learning_objectives || []).length === 0 && (
                <p className="text-[10px] text-slate-400 italic">No objectives — click + Add</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function OutlineActions({ node, onEdit }) {
  const out = node.output_data || {}
  const [modules, setModules] = useState([])

  useEffect(() => {
    setModules((out.modules || []).map((m, i) => ({ ...m, _key: m.id || `mod-${i}` })))
  }, [node.output_data])

  function updateModule(index, updated) {
    setModules(prev => prev.map((m, i) => i === index ? { ...updated, _key: m._key } : m))
  }

  function removeModule(index) {
    setModules(prev => prev.filter((_, i) => i !== index))
  }

  function moveModule(index, dir) {
    setModules(prev => {
      const next = [...prev]
      const j = index + dir
      if (j < 0 || j >= next.length) return prev
      ;[next[index], next[j]] = [next[j], next[index]]
      return next
    })
  }

  function addModule() {
    const newMod = {
      id: `mod-new-${Date.now()}`,
      _key: `mod-new-${Date.now()}`,
      title: '',
      duration_minutes: 30,
      activity_type: 'lecture',
      learning_objectives: [],
    }
    setModules(prev => [...prev, newMod])
  }

  function handleApprove() {
    const cleaned = modules.map(({ _key, ...rest }) => rest)
    onEdit({ ...out, modules: cleaned })
  }

  const totalMinutes = modules.reduce((s, m) => s + (m.duration_minutes || 0), 0)

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 leading-relaxed">
        Review and edit modules. You can reorder, rename, adjust timing, change activity type, and edit learning objectives.
      </p>

      <div className="flex gap-3 text-xs text-slate-500">
        <span>{modules.length} modules</span>
        <span>·</span>
        <span>{totalMinutes} min total</span>
        {out.balance_achieved !== undefined && (
          <>
            <span>·</span>
            <span>{Math.round(out.balance_achieved * 100)}% hands-on</span>
          </>
        )}
      </div>

      {out.pedagogical_warnings?.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded p-2">
          <p className="text-[10px] text-amber-600 uppercase mb-1">Pedagogical Warnings</p>
          {out.pedagogical_warnings.map((w, i) => <p key={i} className="text-xs text-amber-700">• {w}</p>)}
        </div>
      )}

      <div className="space-y-1.5 max-h-80 overflow-y-auto pr-0.5">
        {modules.map((m, i) => (
          <ModuleEditor
            key={m._key}
            module={m}
            index={i}
            total={modules.length}
            onChange={(updated) => updateModule(i, updated)}
            onRemove={removeModule}
            onMove={moveModule}
          />
        ))}
      </div>

      <button
        onClick={addModule}
        className="w-full py-2 border-2 border-dashed border-slate-300 rounded-lg text-xs text-slate-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        + Add Module
      </button>

      <button
        onClick={handleApprove}
        className="w-full py-2.5 bg-green-600 hover:bg-green-700 rounded text-xs font-semibold text-white transition-colors"
      >
        Approve Outline & Generate Scripts →
      </button>
    </div>
  )
}

// ── Conflict Action UI ─────────────────────────────────────────────────────────

function ConflictActions({ node, onDecide }) {
  const out = node.output_data || {}
  const disagreements = out.disagreements || []
  const alreadyResolved = !!(out.human_decisions || out.human_decision)

  // Only non-factual / non-AI-resolved disagreements need a human choice
  const needsHuman = disagreements.filter(d => (d.human_options || []).length > 0)
  const [selections, setSelections] = useState({})

  const allSelected = needsHuman.every(d => selections[d.topic])
  const selectedCount = Object.keys(selections).length

  function handleSelect(topic, option) {
    setSelections(prev => ({ ...prev, [topic]: option }))
  }

  function handleSubmit() {
    if (needsHuman.length > 0) {
      onDecide(selections)
    } else {
      onDecide('all_agreed')
    }
  }

  return (
    <div className="space-y-3">
      <ReviewPanel outputData={out} />

      {(out.agreements || []).length > 0 && (
        <Section title={`${out.agreements.length} Agreement${out.agreements.length > 1 ? 's' : ''}`} defaultOpen={false}>
          {out.agreements.map((a, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs font-semibold text-green-700">{a.topic}</p>
              <p className="text-xs text-slate-600 mt-0.5">{a.shared_recommendation}</p>
            </div>
          ))}
        </Section>
      )}

      {disagreements.length > 0 ? (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">
            {disagreements.length} Disagreement{disagreements.length > 1 ? 's' : ''}{needsHuman.length > 0 ? ' — Select an option for each' : ''}
          </p>

          {disagreements.map((d, i) => (
            <ConflictCard
              key={d.topic || i}
              disagreement={d}
              selected={alreadyResolved ? (out.human_decisions?.[d.topic] || out.human_decision) : (selections[d.topic] || null)}
              onSelect={(opt) => handleSelect(d.topic, opt)}
              disabled={alreadyResolved}
            />
          ))}

          {!alreadyResolved && needsHuman.length > 0 && (
            <button
              onClick={handleSubmit}
              disabled={!allSelected}
              className={`w-full py-2.5 rounded text-xs font-semibold text-white transition-colors ${
                allSelected ? 'bg-blue-600 hover:bg-blue-700' : 'bg-slate-300 cursor-not-allowed'
              }`}
            >
              {allSelected
                ? `Submit ${needsHuman.length} Decision${needsHuman.length > 1 ? 's' : ''} →`
                : `Select all options first (${selectedCount}/${needsHuman.length})`
              }
            </button>
          )}

          {!alreadyResolved && needsHuman.length === 0 && (
            <button
              onClick={handleSubmit}
              className="w-full py-2.5 bg-green-600 hover:bg-green-700 rounded text-xs font-semibold text-white transition-colors"
            >
              Confirm — All Conflicts Resolved by AI →
            </button>
          )}

          {alreadyResolved && (
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <p className="text-xs text-green-700 font-semibold">Decisions submitted ✓</p>
            </div>
          )}
        </div>
      ) : (
        <div>
          <p className="text-xs text-green-600 mb-2">All reviewers agree — no conflicts to resolve.</p>
          <button
            onClick={() => onDecide('all_agreed')}
            className="w-full py-2 bg-green-600 hover:bg-green-700 rounded text-xs font-semibold text-white transition-colors"
          >
            Confirm & Continue
          </button>
        </div>
      )}
    </div>
  )
}

// ── Script / Review viewers ─────────────────────────────────────────────────────

function ScriptViewer({ outputData }) {
  const sections = outputData?.sections || []
  return (
    <div className="space-y-3">
      <div className="flex gap-3 text-xs text-slate-500">
        <span>{sections.length} sections</span>
        <span>· {outputData?.total_duration_minutes} min</span>
      </div>
      {sections.map((s, i) => (
        <div key={i} className="bg-slate-50 border border-slate-200 rounded p-3">
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-xs font-semibold text-slate-800">{s.title}</p>
            <span className="text-[10px] text-slate-400">{s.duration_minutes}min</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed mb-2">{s.speaker_notes}</p>
          {s.key_points?.length > 0 && (
            <div className="mb-2">
              <p className="text-[10px] text-slate-400 uppercase mb-1">Key Points</p>
              {s.key_points.map((kp, j) => <p key={j} className="text-xs text-slate-700">• {kp}</p>)}
            </div>
          )}
          {s.activity && (
            <div className="bg-blue-50 border border-blue-200 rounded p-2 mt-2">
              <p className="text-[10px] text-blue-600 uppercase mb-0.5">Activity: {s.activity.type}</p>
              <p className="text-xs text-blue-700">{s.activity.description}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function ReviewViewer({ outputData }) {
  const VERDICT_CLS = {
    approve: 'bg-green-100 text-green-700',
    flag: 'bg-amber-100 text-amber-700',
    reject: 'bg-red-100 text-red-700',
  }
  const SEV_CLS = { info: 'text-blue-600', warning: 'text-amber-600', critical: 'text-red-600' }
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${VERDICT_CLS[outputData?.verdict] || 'bg-slate-100 text-slate-600'}`}>
          {outputData?.verdict}
        </span>
        <span className="text-xs text-slate-500">{Math.round((outputData?.confidence || 0) * 100)}% confidence</span>
      </div>
      <p className="text-xs text-slate-700 leading-relaxed">{outputData?.reasoning}</p>
      {(outputData?.findings || []).map((f, i) => (
        <div key={i} className="bg-slate-50 border border-slate-200 rounded p-2 text-xs">
          <p>
            <span className={`font-bold ${SEV_CLS[f.severity] || 'text-slate-500'}`}>[{f.severity}]</span>
            {' '}<span className="text-slate-500">{f.category}</span>
          </p>
          <p className="text-slate-700 mt-0.5">{f.description}</p>
          <p className="text-slate-500 mt-0.5">→ {f.suggestion}</p>
        </div>
      ))}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function NodeDetail({ node, onApprove, onEdit, onDecide, onChat }) {
  if (!node) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 bg-slate-50">
        <p className="text-sm text-slate-400">No node selected</p>
        <p className="text-xs text-slate-300">Click a node in the graph to inspect it</p>
      </div>
    )
  }

  const status = STATUS_META[node.status] || { label: node.status, cls: 'bg-slate-100 text-slate-600' }
  const isAwaiting = node.status === 'awaiting_human'

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-white">

      {/* Header */}
      <div className="p-4 border-b border-slate-200 shrink-0">
        <div className="flex items-start gap-2 mb-3">
          <h2 className="text-sm font-bold text-slate-900 flex-1 leading-tight">{node.label}</h2>
          <button
            onClick={onChat}
            title="Chat with this agent"
            className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-600 transition-colors shrink-0"
          >
            💬 Chat
          </button>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-2">
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${status.cls}`}>
            {status.label}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${AUTONOMY_CLS[node.autonomy] || 'bg-slate-100 text-slate-600'}`}>
            {node.autonomy}
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-500">{node.type}</span>
        </div>

        <p className="text-[10px] text-slate-400 italic">{AUTONOMY_DESC[node.autonomy]}</p>

        {node.reasoning && (
          <p className="text-xs text-slate-500 mt-2 leading-relaxed border-t border-slate-100 pt-2">{node.reasoning}</p>
        )}

        {node.output_data?.error && (
          <div className="mt-2 bg-red-50 border border-red-200 rounded p-2">
            <p className="text-xs text-red-700">{node.output_data.error}</p>
          </div>
        )}
      </div>

      {/* Human action UI — shown when awaiting */}
      {isAwaiting && (
        <div className="p-4 border-b border-amber-200 bg-amber-50 shrink-0">
          <p className="text-[10px] font-semibold text-amber-600 uppercase tracking-wide mb-3">
            ↓ Your input required
          </p>
          {node.type === 'audience' && (
            <AudienceActions node={node} onApprove={() => onApprove(node.id)} onEdit={(out) => onEdit(node.id, out)} />
          )}
          {node.type === 'catalog' && (
            <CatalogActions node={node} onApprove={() => onApprove(node.id)} />
          )}
          {node.type === 'outline' && (
            <OutlineActions node={node} onEdit={(out) => onEdit(node.id, out)} />
          )}
          {node.type === 'conflict' && (
            <ConflictActions node={node} onDecide={(d) => onDecide(node.id, d)} />
          )}
          {!['audience', 'catalog', 'outline', 'conflict'].includes(node.type) && (
            <button
              onClick={() => onApprove(node.id)}
              className="w-full py-2.5 bg-green-600 hover:bg-green-700 rounded text-xs font-semibold text-white transition-colors"
            >
              Approve ✓
            </button>
          )}
        </div>
      )}

      {/* Output data — rendered intelligently per node type */}
      <div className="p-4 space-y-2 flex-1">
        {node.status === 'completed' && node.output_data && Object.keys(node.output_data).length > 0 && (
          <>
            {node.type === 'script' && (
              <Section title="Script" defaultOpen={true}>
                <ScriptViewer outputData={node.output_data} />
              </Section>
            )}
            {['review_technical', 'review_pedagogy', 'review_business'].includes(node.type) && (
              <Section title="Review Findings" defaultOpen={true}>
                <ReviewViewer outputData={node.output_data} />
              </Section>
            )}
            {node.type === 'research' && (
              <Section title="Topic Map" defaultOpen={true}>
                <div className="space-y-2">
                  {(node.output_data.concepts || []).map((c, i) => (
                    <div key={i} className="bg-slate-50 border border-slate-200 rounded p-2 text-xs">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold text-slate-800">{c.name}</p>
                        <span className="text-slate-400">depth: {c.depth}</span>
                        <span className="text-slate-400 ml-auto">{c.estimated_minutes}min</span>
                      </div>
                      <p className="text-slate-600">{c.description}</p>
                      {c.subtopics?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {c.subtopics.map((s, j) => <span key={j} className="px-1 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] text-slate-600">{s}</span>)}
                        </div>
                      )}
                    </div>
                  ))}
                  {node.output_data.coverage_warnings?.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded p-2">
                      {node.output_data.coverage_warnings.map((w, i) => <p key={i} className="text-xs text-amber-700">⚠ {w}</p>)}
                    </div>
                  )}
                </div>
              </Section>
            )}
            {node.type === 'audience' && (
              <Section title="Audience Profile" defaultOpen={true}>
                <div className="space-y-2 text-xs">
                  {node.output_data.profile_summary && (
                    <p className="text-slate-700 leading-relaxed">{node.output_data.profile_summary}</p>
                  )}
                  {[
                    ['assumed_knowledge', 'Assumed Knowledge'],
                    ['knowledge_gaps', 'Knowledge Gaps'],
                    ['pain_points', 'Pain Points'],
                    ['preferred_modalities', 'Preferred Modalities'],
                    ['engagement_strategies', 'Engagement Strategies'],
                  ].map(([key, label]) => (
                    node.output_data[key]?.length > 0 && (
                      <div key={key}>
                        <p className="text-[10px] text-slate-400 uppercase mb-1">{label}</p>
                        {node.output_data[key].map((item, i) => <p key={i} className="text-slate-700">• {item}</p>)}
                      </div>
                    )
                  ))}
                </div>
              </Section>
            )}
            {!['script', 'review_technical', 'review_pedagogy', 'review_business', 'research', 'audience'].includes(node.type) && (
              <Section title="Output Data" defaultOpen={true}>
                <JsonBlock data={node.output_data} />
              </Section>
            )}
          </>
        )}

        {node.input_data && Object.keys(node.input_data).length > 0 && (
          <Section title="Input Data">
            <JsonBlock data={node.input_data} />
          </Section>
        )}
      </div>
    </div>
  )
}
