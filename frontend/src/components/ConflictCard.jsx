const CONFLICT_COLORS = {
  factual:   'bg-blue-100 text-blue-700',
  priority:  'bg-orange-100 text-orange-700',
  subjective:'bg-purple-100 text-purple-700',
}

export default function ConflictCard({ disagreement, selected, onSelect, disabled }) {
  const { topic, positions = {}, conflict_type, ai_resolution, ai_assessment, human_options = [] } = disagreement
  const isFactual = conflict_type === 'factual'

  return (
    <div className={`border rounded-xl p-4 mb-3 transition-colors ${
      selected ? 'border-blue-400 bg-blue-50' :
      isFactual ? 'border-green-200 bg-green-50' :
      'border-gray-200 bg-white'
    }`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-semibold text-gray-800">{topic}</span>
        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${CONFLICT_COLORS[conflict_type] || 'bg-gray-100 text-gray-600'}`}>
          {conflict_type}
        </span>
        {isFactual && <span className="ml-auto text-xs text-green-600 font-semibold">✓ AI resolved</span>}
      </div>

      {/* Reviewer positions */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {Object.entries(positions).map(([reviewer, pos]) => (
          <div key={reviewer} className="bg-gray-50 border border-gray-100 rounded-lg p-2">
            <p className="text-[10px] text-gray-400 uppercase font-semibold mb-0.5">{reviewer}</p>
            <p className="text-xs text-gray-700 leading-snug">{pos}</p>
          </div>
        ))}
      </div>

      {/* AI resolution (factual) */}
      {ai_resolution && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-2.5 mb-2">
          <p className="text-[10px] text-blue-600 uppercase font-semibold mb-0.5">AI Resolution</p>
          <p className="text-xs text-blue-800">{ai_resolution}</p>
        </div>
      )}

      {/* AI assessment + human options */}
      {!isFactual && (
        <>
          {ai_assessment && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 mb-3">
              <p className="text-[10px] text-gray-500 uppercase font-semibold mb-0.5">Why the AI can't decide</p>
              <p className="text-xs text-gray-600 leading-relaxed">{ai_assessment}</p>
            </div>
          )}

          {!disabled && (
            <div>
              <p className="text-[10px] text-gray-500 uppercase font-semibold mb-2">Choose an option</p>
              <div className="space-y-1.5">
                {human_options.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => onSelect(opt)}
                    className={`w-full text-left text-xs rounded-lg px-3 py-2.5 border transition-colors ${
                      selected === opt
                        ? 'bg-blue-600 border-blue-600 text-white font-semibold'
                        : 'bg-white border-gray-200 text-gray-700 hover:border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {disabled && selected && (
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <p className="text-[10px] text-green-600 uppercase font-semibold mb-0.5">Your decision</p>
              <p className="text-xs text-green-800">{selected}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
