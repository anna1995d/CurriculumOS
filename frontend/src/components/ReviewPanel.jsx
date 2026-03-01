const VERDICT_COLORS = {
  approve: 'bg-green-100 text-green-700',
  flag:    'bg-amber-100 text-amber-700',
  reject:  'bg-red-100 text-red-700',
}

export default function ReviewPanel({ outputData }) {
  const verdicts = outputData?.overall_verdicts || {}
  return (
    <div className="flex gap-2 flex-wrap mb-3">
      {['technical', 'pedagogy', 'business'].map(r => (
        <span key={r} className={`px-2 py-0.5 rounded text-xs font-semibold ${VERDICT_COLORS[verdicts[r]] || 'bg-gray-100 text-gray-500'}`}>
          {r}: {verdicts[r] || '—'}
        </span>
      ))}
    </div>
  )
}
