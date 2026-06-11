import { useState } from 'react'
import { api } from '../api'

export default function ChatPanel({ session }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const ask = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    const q = question.trim()
    setMessages((m) => [...m, { role: 'agent', content: q }])
    setQuestion('')
    setLoading(true)
    try {
      const result = await api.chat(session.session_id, session.process.process_id, q)
      setMessages((m) => [
        ...m,
        { role: 'coach', content: result.answer, sources: result.sources },
      ])
    } catch (err) {
      setMessages((m) => [...m, { role: 'coach', content: `Error: ${err.message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card chat-panel">
      <h2>Ask the process assistant</h2>
      <div className="messages">
        {messages.length === 0 && (
          <p className="hint">
            Ask anything about policy or what to say — e.g. "Customer wants a refund for a
            charge from 3 months ago, what do I do?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <strong>{m.role === 'agent' ? 'You' : 'Coach'}:</strong> {m.content}
            {m.sources && m.sources.length > 0 && (
              <div className="sources">Source: {m.sources.join(', ')}</div>
            )}
          </div>
        ))}
        {loading && <div className="message coach">Coach is thinking…</div>}
      </div>
      <form onSubmit={ask}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type a question…"
        />
        <button type="submit" disabled={loading}>
          Ask
        </button>
      </form>
    </div>
  )
}
