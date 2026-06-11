import { useState } from 'react'
import { api } from '../api'

export default function FlowPanel({ session, setSession }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { current_step: step, finished } = session

  const advance = async (chosenOptionNextStepId) => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.advanceStep(session.session_id, chosenOptionNextStepId)
      setSession({ ...session, current_step: result.current_step, finished: result.finished })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card flow-panel">
      <h2>Call steps — {session.process.name}</h2>
      <div className="step">
        <h3>{step.title}</h3>
        <p>{step.instructions}</p>
      </div>

      {error && <p className="error">{error}</p>}

      {finished || step.is_end ? (
        <p className="finished">✅ Call complete.</p>
      ) : step.options && step.options.length > 0 ? (
        <div className="options">
          {step.options.map((opt) => (
            <button
              key={opt.next_step_id}
              disabled={loading}
              onClick={() => advance(opt.next_step_id)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      ) : (
        <button disabled={loading} onClick={() => advance(null)}>
          Next step →
        </button>
      )}
    </div>
  )
}
