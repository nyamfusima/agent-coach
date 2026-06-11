import { useEffect, useState } from 'react'
import { api } from '../api'

export default function ProcessSelector({ onStart }) {
  const [processes, setProcesses] = useState([])
  const [agentId, setAgentId] = useState('')
  const [processId, setProcessId] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .listProcesses()
      .then((procs) => {
        setProcesses(procs)
        if (procs.length) setProcessId(procs[0].process_id)
      })
      .catch((e) => setError(e.message))
  }, [])

  const handleStart = (e) => {
    e.preventDefault()
    if (!agentId || !processId) return
    onStart(agentId, processId)
  }

  return (
    <div className="card process-selector">
      <h2>Start a call</h2>
      {error && <p className="error">Couldn't reach the API: {error}</p>}
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
          <select value={processId} onChange={(e) => setProcessId(e.target.value)}>
            {processes.map((p) => (
              <option key={p.process_id} value={p.process_id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        {processId && (
          <p className="hint">
            {processes.find((p) => p.process_id === processId)?.description}
          </p>
        )}
        <button type="submit" disabled={!processes.length}>
          Start call
        </button>
      </form>
    </div>
  )
}
