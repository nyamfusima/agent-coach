import { useEffect, useState } from 'react'
import { api } from '../api'

export default function ProcessSelector({ onStart }) {
  const [processes, setProcesses] = useState([])
  const [agentId, setAgentId] = useState('')
  const [processId, setProcessId] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .listProcesses()
      .then((procs) => {
        if (cancelled) return
        setProcesses(procs)
        if (procs.length) setProcessId(procs[0].process_id)
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  const handleStart = (e) => {
    e.preventDefault()
    if (!agentId || !processId) return
    onStart(agentId, processId)
  }

  return (
    <div className="card process-selector">
      <h2>Start a call</h2>

      {error && (
        <p className="error">
          Couldn't reach the API — is the backend running on :8000? ({error})
        </p>
      )}

      {!error && loading && <p className="notice">Loading call types…</p>}

      {!error && !loading && processes.length === 0 && (
        <p className="notice">
          No call types found. Add a flow under <code>data/flows/</code> and
          restart the backend.
        </p>
      )}

      <form onSubmit={handleStart}>
        <label>
          Agent ID
          <input
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="e.g. agent_42"
            required
          />
        </label>
        <label>
          Call type
          <select
            value={processId}
            onChange={(e) => setProcessId(e.target.value)}
            disabled={!processes.length}
          >
            {processes.length === 0 ? (
              <option value="">
                {loading
                  ? 'Loading call types…'
                  : error
                  ? '— couldn’t load call types —'
                  : '— no call types available —'}
              </option>
            ) : (
              processes.map((p) => (
                <option key={p.process_id} value={p.process_id}>
                  {p.name}
                </option>
              ))
            )}
          </select>
        </label>
        {processId && (
          <p className="hint">
            {processes.find((p) => p.process_id === processId)?.description}
          </p>
        )}
        <button type="submit" className="block" disabled={!processes.length || !agentId}>
          Start call
        </button>
      </form>
    </div>
  )
}
