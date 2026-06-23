import { useState } from 'react'
import { saveProfile } from '../profile'

export default function Login({ onSave }) {
  const [name, setName] = useState('')
  const [agentId, setAgentId] = useState('')
  const [team, setTeam] = useState('')

  const submit = (e) => {
    e.preventDefault()
    if (!name.trim() || !agentId.trim()) return
    const profile = { name: name.trim(), agentId: agentId.trim(), team: team.trim() }
    saveProfile(profile)
    onSave(profile)
  }

  return (
    <div className="card login">
      <p className="login-promise">The right answer, the moment you need it.</p>
      <h2>Sign in to start your shift</h2>
      <p className="hint">
        Your details stay on this device and are attached to your call sessions for
        supervisor reporting. No password needed.
      </p>
      <form onSubmit={submit}>
        <label>
          Your name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Jane Doe"
            required
          />
        </label>
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
          Team
          <input
            value={team}
            onChange={(e) => setTeam(e.target.value)}
            placeholder="e.g. Billing Team A"
          />
        </label>
        <button type="submit" className="block" disabled={!name.trim() || !agentId.trim()}>
          Start working
        </button>
      </form>
    </div>
  )
}
