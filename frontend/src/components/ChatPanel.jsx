import { useState } from 'react'
import { api } from '../api'
import { AIInputWithFile } from './ui/AIInputWithFile'
import Spinner from './Spinner'

export default function ChatPanel({ session, profile }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const processId = session.process.process_id

  const ask = async (message, file) => {
    const q = message.trim()
    if (!q && !file) return

    setMessages((m) => [...m, { role: 'agent', content: q, fileName: file?.name }])

    if (!q) {
      setMessages((m) => [
        ...m,
        {
          role: 'coach',
          content:
            'Add a question describing what you need help with. File-only requests aren’t supported yet.',
        },
      ])
      return
    }

    setLoading(true)
    try {
      const result = await api.chat(session.session_id, processId, q, profile)
      setMessages((m) => [
        ...m,
        {
          role: 'coach',
          content: result.answer,
          sources: result.sources,
          lowConfidence: result.low_confidence,
          question: q,
          flagged: false,
        },
      ])
    } catch (err) {
      setMessages((m) => [...m, { role: 'coach', content: `Error: ${err.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const flag = async (index) => {
    const msg = messages[index]
    if (!msg || msg.flagged) return
    // optimistic
    setMessages((m) => m.map((x, i) => (i === index ? { ...x, flagged: true } : x)))
    try {
      await api.flagAnswer({
        sessionId: session.session_id,
        processId,
        question: msg.question || '',
        answer: msg.content,
        profile,
      })
    } catch {
      setMessages((m) => m.map((x, i) => (i === index ? { ...x, flagged: false } : x)))
    }
  }

  return (
    <div className="card chat-panel">
      <h2>Ask AgeCX</h2>
      <div className="messages">
        {messages.length === 0 && (
          <p className="hint">
            Ask anything about policy or what to say. For example: "Customer wants a refund
            for a charge from 3 months ago, what do I do?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <strong>{m.role === 'agent' ? 'You' : 'Coach'}:</strong> {m.content}
            {m.fileName && <div className="attachment">📎 {m.fileName}</div>}

            {m.lowConfidence && (
              <div className="low-confidence">
                ⚠️ Low confidence. Consider escalating or confirming with a supervisor.
              </div>
            )}

            {m.sources && m.sources.length > 0 && (
              <div className="sources">Source: {m.sources.join(', ')}</div>
            )}

            {m.role === 'coach' && m.question && (
              <div className="answer-actions">
                <button
                  type="button"
                  className={`thumbs-down ${m.flagged ? 'is-flagged' : ''}`}
                  onClick={() => flag(i)}
                  disabled={m.flagged}
                  title="Flag this answer as unhelpful for supervisor review"
                >
                  {m.flagged ? '✓ Flagged for review' : '👎 Not helpful'}
                </button>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message coach">
            <Spinner label="Coach is thinking…" />
          </div>
        )}
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
