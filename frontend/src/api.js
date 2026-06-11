const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

export const api = {
  listProcesses: () => request('/processes'),
  startSession: (agentId, processId) =>
    request('/sessions/start', {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, process_id: processId }),
    }),
  advanceStep: (sessionId, chosenOptionNextStepId) =>
    request('/sessions/advance', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        chosen_option_next_step_id: chosenOptionNextStepId || null,
      }),
    }),
  chat: (sessionId, processId, question) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, process_id: processId, question }),
    }),
}
