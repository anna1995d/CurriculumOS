import { useState } from 'react'

const STEPS = ['Topic', 'Audience', 'Format', 'Goals', 'Review']

const TOPIC_AREAS = ['ML', 'Data Science', 'Ethics', 'Programming', 'Applied AI', 'Other']
const AUDIENCES = ['Executives', 'Technical PMs', 'Junior Devs', 'Senior Engineers', 'Non-technical']
const CLASS_SIZES = [
  { value: 'small', label: 'Small (<15)' },
  { value: 'medium', label: 'Medium (15–40)' },
  { value: 'large', label: 'Large (40+)' },
]
const DURATIONS = ['1hr talk', 'half-day', 'full-day', 'multi-day']
const FORMATS = [
  { value: 'in-person', label: 'In-Person' },
  { value: 'virtual', label: 'Virtual' },
  { value: 'self-paced', label: 'Self-Paced' },
]

const INITIAL = {
  title: '',
  topic_area: '',
  description: '',
  audience: '',
  prerequisites: [''],
  class_size: '',
  duration: '',
  format: '',
  balance: 0.5,
  learning_objectives: ['', '', ''],
  outcome_description: '',
}

function Label({ children, hint }) {
  return (
    <div className="mb-1.5">
      <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide">{children}</label>
      {hint && <p className="text-[10px] text-slate-400 mt-0.5">{hint}</p>}
    </div>
  )
}

function Input({ value, onChange, placeholder, maxLength }) {
  return (
    <input
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      maxLength={maxLength}
      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition-colors"
    />
  )
}

function Select({ value, onChange, options, placeholder }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition-colors"
    >
      <option value="">{placeholder}</option>
      {options.map(o => (
        <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>
          {typeof o === 'string' ? o : o.label}
        </option>
      ))}
    </select>
  )
}

function Textarea({ value, onChange, placeholder, maxLength, rows = 3 }) {
  return (
    <div>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        rows={rows}
        className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition-colors resize-none"
      />
      {maxLength && (
        <p className="text-[10px] text-slate-400 text-right mt-0.5">{value.length}/{maxLength}</p>
      )}
    </div>
  )
}

function RadioGroup({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => {
        const val = typeof o === 'string' ? o : o.value
        const lbl = typeof o === 'string' ? o : o.label
        return (
          <button
            key={val}
            type="button"
            onClick={() => onChange(val)}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
              value === val
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'bg-white border-slate-300 text-slate-700 hover:border-blue-400 hover:bg-blue-50'
            }`}
          >
            {lbl}
          </button>
        )
      })}
    </div>
  )
}

// ── Steps ─────────────────────────────────────────────────────────────────────

function StepTopic({ form, set }) {
  return (
    <div className="space-y-5">
      <div>
        <Label hint="What will this course be called?">Course Title</Label>
        <Input value={form.title} onChange={v => set('title', v)} placeholder="e.g. Introduction to Prompt Engineering" />
      </div>
      <div>
        <Label hint="Which domain does this course belong to?">Topic Area</Label>
        <Select value={form.topic_area} onChange={v => set('topic_area', v)} options={TOPIC_AREAS} placeholder="Select topic area" />
      </div>
      <div>
        <Label hint="Describe what this course covers (max 500 chars). Be specific.">Description</Label>
        <Textarea value={form.description} onChange={v => set('description', v)} placeholder="A concise description of the course…" maxLength={500} rows={4} />
      </div>
    </div>
  )
}

function StepAudience({ form, set }) {
  function updatePrereq(i, val) {
    const updated = [...form.prerequisites]
    updated[i] = val
    set('prerequisites', updated)
  }
  function addPrereq() {
    set('prerequisites', [...form.prerequisites, ''])
  }
  function removePrereq(i) {
    set('prerequisites', form.prerequisites.filter((_, idx) => idx !== i))
  }

  return (
    <div className="space-y-5">
      <div>
        <Label hint="Who is the primary audience for this course?">Target Audience</Label>
        <Select value={form.audience} onChange={v => set('audience', v)} options={AUDIENCES} placeholder="Select audience" />
      </div>
      <div>
        <Label hint="What should learners already know? Leave empty if no prerequisites.">Prerequisites</Label>
        <div className="space-y-2">
          {form.prerequisites.map((p, i) => (
            <div key={i} className="flex gap-2">
              <Input value={p} onChange={v => updatePrereq(i, v)} placeholder={`Prerequisite ${i + 1}`} />
              {form.prerequisites.length > 1 && (
                <button onClick={() => removePrereq(i)} className="text-slate-400 hover:text-red-500 px-2 text-lg leading-none">×</button>
              )}
            </div>
          ))}
          <button onClick={addPrereq} className="text-xs text-blue-600 hover:text-blue-800">+ Add prerequisite</button>
        </div>
      </div>
      <div>
        <Label hint="Approximate number of learners in a session.">Class Size</Label>
        <RadioGroup options={CLASS_SIZES} value={form.class_size} onChange={v => set('class_size', v)} />
      </div>
    </div>
  )
}

function StepFormat({ form, set }) {
  return (
    <div className="space-y-5">
      <div>
        <Label hint="How long will this course run?">Duration</Label>
        <Select value={form.duration} onChange={v => set('duration', v)} options={DURATIONS} placeholder="Select duration" />
      </div>
      <div>
        <Label hint="How will the course be delivered?">Delivery Format</Label>
        <RadioGroup options={FORMATS} value={form.format} onChange={v => set('format', v)} />
      </div>
      <div>
        <Label hint="Where on the spectrum should this course sit?">
          Content Balance
        </Label>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-slate-500">Conceptual</span>
          <input
            type="range"
            min={0} max={1} step={0.05}
            value={form.balance}
            onChange={e => set('balance', parseFloat(e.target.value))}
            className="flex-1 accent-blue-600"
          />
          <span className="text-xs text-slate-500">Hands-on</span>
        </div>
        <p className="text-[10px] text-slate-400 text-center mt-1">
          {form.balance < 0.3 ? 'Mostly conceptual / lecture-based' :
           form.balance > 0.7 ? 'Mostly hands-on / practical' :
           'Balanced mix of concept and practice'} ({Math.round(form.balance * 100)}%)
        </p>
      </div>
    </div>
  )
}

function StepGoals({ form, set }) {
  function updateObj(i, val) {
    const updated = [...form.learning_objectives]
    updated[i] = val
    set('learning_objectives', updated)
  }

  return (
    <div className="space-y-5">
      <div>
        <Label hint="What will learners be able to do after this course? (up to 3)">Learning Objectives</Label>
        <div className="space-y-2">
          {form.learning_objectives.map((obj, i) => (
            <Input
              key={i}
              value={obj}
              onChange={v => updateObj(i, v)}
              placeholder={`Objective ${i + 1}: e.g. "Write effective prompts for summarization tasks"`}
            />
          ))}
        </div>
      </div>
      <div>
        <Label hint="What does success look like after completing this course?">Outcome Description</Label>
        <Textarea
          value={form.outcome_description}
          onChange={v => set('outcome_description', v)}
          placeholder="Learners will be able to…"
          rows={4}
        />
      </div>
    </div>
  )
}

function StepReview({ form }) {
  const objectives = form.learning_objectives.filter(Boolean)
  const prereqs = form.prerequisites.filter(Boolean)

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Review your brief before generating the pipeline.</p>
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3 text-sm">
        <Row label="Title" value={form.title} />
        <Row label="Topic Area" value={form.topic_area} />
        <Row label="Description" value={form.description} />
        <Row label="Audience" value={form.audience} />
        <Row label="Prerequisites" value={prereqs.length ? prereqs.join(', ') : 'None'} />
        <Row label="Class Size" value={form.class_size} />
        <Row label="Duration" value={form.duration} />
        <Row label="Format" value={form.format} />
        <Row label="Balance" value={`${Math.round(form.balance * 100)}% hands-on`} />
        <Row label="Objectives" value={objectives.join(' / ') || '—'} />
        <Row label="Outcome" value={form.outcome_description} />
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex gap-3">
      <span className="text-slate-400 w-28 shrink-0 text-xs uppercase">{label}</span>
      <span className="text-slate-700 text-xs">{value}</span>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function BriefWizard({ onSubmit, onStart, pipelineId, submitting }) {
  const [step, setStep] = useState(0)
  const [form, setForm] = useState(INITIAL)

  function set(key, value) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  function canNext() {
    if (step === 0) return form.title && form.topic_area && form.description
    if (step === 1) return form.audience && form.class_size
    if (step === 2) return form.duration && form.format
    if (step === 3) return form.learning_objectives.some(Boolean) && form.outcome_description
    return true
  }

  function handleSubmit() {
    const brief = {
      ...form,
      prerequisites: form.prerequisites.filter(Boolean),
      learning_objectives: form.learning_objectives.filter(Boolean),
    }
    onSubmit(brief)
  }

  const stepProps = { form, set }

  return (
    <div className="flex items-center justify-center min-h-screen p-6 bg-slate-50">
      <div className="w-full max-w-xl">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-900">CurriculumOS</h1>
          <p className="text-sm text-slate-500 mt-1">AI-powered course development pipeline</p>
        </div>

        {/* Pipeline created state */}
        {pipelineId && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center shadow-sm">
            <div className="text-3xl mb-2">✓</div>
            <p className="text-sm font-semibold text-green-700 mb-1">Pipeline Created</p>
            <p className="text-xs text-slate-400 mb-4 font-mono">{pipelineId}</p>
            <button
              onClick={onStart}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-bold text-white transition-colors shadow-sm"
            >
              Start Pipeline →
            </button>
          </div>
        )}

        {!pipelineId && (
          <>
            {/* Progress */}
            <div className="flex items-center gap-2 mb-6">
              {STEPS.map((s, i) => (
                <div key={s} className="flex items-center gap-2 flex-1 last:flex-none">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                    i < step ? 'bg-green-500 text-white' :
                    i === step ? 'bg-blue-600 text-white' :
                    'bg-slate-200 text-slate-500'
                  }`}>
                    {i < step ? '✓' : i + 1}
                  </div>
                  <span className={`text-xs ${i === step ? 'text-slate-800 font-semibold' : 'text-slate-400'}`}>{s}</span>
                  {i < STEPS.length - 1 && <div className="flex-1 h-px bg-slate-200" />}
                </div>
              ))}
            </div>

            {/* Card */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 mb-4 shadow-sm">
              <h2 className="text-base font-bold text-slate-800 mb-5">{STEPS[step]}</h2>
              {step === 0 && <StepTopic {...stepProps} />}
              {step === 1 && <StepAudience {...stepProps} />}
              {step === 2 && <StepFormat {...stepProps} />}
              {step === 3 && <StepGoals {...stepProps} />}
              {step === 4 && <StepReview {...stepProps} />}
            </div>

            {/* Navigation */}
            <div className="flex gap-3">
              {step > 0 && (
                <button
                  onClick={() => setStep(s => s - 1)}
                  className="px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg text-sm text-slate-700 transition-colors"
                >
                  ← Back
                </button>
              )}
              {step < STEPS.length - 1 && (
                <button
                  onClick={() => setStep(s => s + 1)}
                  disabled={!canNext()}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-lg text-sm font-semibold text-white transition-colors"
                >
                  Next →
                </button>
              )}
              {step === STEPS.length - 1 && (
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-40 rounded-lg text-sm font-semibold text-white transition-colors"
                >
                  {submitting ? 'Generating…' : 'Generate Pipeline'}
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
