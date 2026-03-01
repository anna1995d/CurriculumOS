import { useRef, useState } from 'react'

export default function ChatPanel({ node, onClose, onSendChat }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)
    try {
      const data = await onSendChat(node.id, userMsg)
      setMessages(prev => [...prev, { role: 'agent', content: data.response }])
    } catch {
      setMessages(prev => [...prev, { role: 'error', content: 'Failed to get response.' }])
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white border border-gray-200 rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50" style={{ height: '420px' }}>
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 shrink-0 bg-gray-50">
        <div className="w-2 h-2 rounded-full bg-green-400" />
        <span className="text-sm font-semibold text-gray-800 truncate">{node?.label}</span>
        <button onClick={onClose} className="ml-auto text-gray-400 hover:text-gray-700 text-xl leading-none">×</button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-white">
        {messages.length === 0 && (
          <p className="text-xs text-gray-400 text-center mt-4">Ask this agent anything about its work.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
              m.role === 'user'  ? 'bg-blue-600 text-white' :
              m.role === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
                                   'bg-gray-100 text-gray-800'
            }`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-3 py-2 text-xs text-gray-500">Thinking…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex gap-2 p-3 border-t border-gray-100 shrink-0 bg-gray-50">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-1.5 text-xs text-gray-800 placeholder-gray-400 outline-none focus:border-blue-400"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-lg text-xs font-semibold text-white transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  )
}
