import { useState } from 'react'
import { api } from '../api'
import { AIInputWithFile } from './ui/AIInputWithFile'

export default function ChatPanel({ session }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const ask = async (message, file) => {
    const q = message.trim()
    if (!q && !file) return

    setMessages((m) => [...m, { role: 'agent', content: q, fileName: file?.name }])

    // The backend /chat endpoint is text-only — an attachment is shown in the
    // thread but not uploaded yet. Wire file handling here when the API supports it.
    if (!q) {
      setMessages((m) => [
        ...m,
        {
          role: 'coach',
          content:
            'Add a question describing what you need help with — file-only requests aren’t supported yet.',
        },
      ])
      return
    }

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
            {m.fileName && <div className="attachment">📎 {m.fileName}</div>}
            {m.sources && m.sources.length > 0 && (
              <div className="sources">Source: {m.sources.join(', ')}</div>
            )}
          </div>
        ))}
        {loading && <div className="message coach">Coach is thinking…</div>}
      </div>
      <AIInputWithFile
        placeholder="Type a question…"
        accept="image/*"
        maxFileSize={5}
        disabled={loading}
        onSubmit={ask}
      />
    </div>
  )
}
