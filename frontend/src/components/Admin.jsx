import { useEffect, useState } from 'react'
import { api } from '../api'
import Spinner from './Spinner'
import Logo from './Logo'

function fmtDate(iso) {
  if (!iso) return 'n/a'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? 'n/a' : d.toLocaleString()
}

function fmtDuration(seconds) {
  if (seconds == null) return 'n/a'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${String(s).padStart(2, '0')}s`
}

export default function Admin() {
  const [sessions, setSessions] = useState([])
  const [questions, setQuestions] = useState([])
  const [flagged, setFlagged] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([api.adminSessions(), api.adminQuestions(), api.adminFlagged()])
      .then(([s, q, f]) => {
        if (cancelled) return
        setSessions(s)
        setQuestions(q)
        setFlagged(f)
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="app admin">
      <header className="topbar">
        <div className="brand">
          <Logo />
          <div className="brand-text">
            <span className="brand-name">
              Age<span className="brand-accent">CX</span> <span className="brand-ai">AI</span>
            </span>
            <span className="brand-tag">Supervisor dashboard</span>
          </div>
        </div>
        <a className="link" href="/">
          ← Back to app
        </a>
      </header>

      {error && <p className="error">Couldn't load admin data: {error}</p>}
      {loading && (
        <p className="notice">
          <Spinner label="Loading…" />
        </p>
      )}

      {!loading && !error && (
        <>
          <div className="card">
            <h2>Recent call sessions</h2>
            {sessions.length === 0 ? (
              <p className="hint">No sessions yet.</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Team</th>
                    <th>Call type</th>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Questions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s) => (
                    <tr key={s.session_id}>
                      <td>{s.agent_name || s.agent_id}</td>
                      <td>{s.team_name || 'n/a'}</td>
                      <td>{s.process_name}</td>
                      <td>{fmtDate(s.created_at)}</td>
                      <td>{fmtDuration(s.duration_seconds)}</td>
                      <td>{s.message_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="card">
            <h2>Most asked questions (by call type)</h2>
            {questions.length === 0 ? (
              <p className="hint">No questions logged yet.</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Call type</th>
                    <th>Question</th>
                    <th>Times asked</th>
                  </tr>
                </thead>
                <tbody>
                  {questions.map((q, i) => (
                    <tr key={i}>
                      <td>{q.process_name}</td>
                      <td>{q.question}</td>
                      <td>{q.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="card">
            <h2>Flagged answers (for knowledge-base review)</h2>
            {flagged.length === 0 ? (
              <p className="hint">No flagged answers. 🎉</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>When</th>
                    <th>Agent</th>
                    <th>Question</th>
                    <th>Answer given</th>
                  </tr>
                </thead>
                <tbody>
                  {flagged.map((f) => (
                    <tr key={f.id}>
                      <td>{fmtDate(f.created_at)}</td>
                      <td>{f.agent_name || f.agent_id || 'n/a'}</td>
                      <td>{f.question}</td>
                      <td className="answer-cell">{f.answer}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
