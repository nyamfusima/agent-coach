const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = await res.text()
    try {
      detail = JSON.parse(detail).detail ?? detail
    } catch {
      /* leave raw text */
    }
    throw new Error(detail || `API error ${res.status}`)
  }
  return res.json()
}

export const api = {
  listProcesses: () => request('/processes'),

  startSession: (profile, processId) =>
    request('/sessions/start', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: profile?.agentId || '',
        agent_name: profile?.name || null,
        team_name: profile?.team || null,
        process_id: processId,
      }),
    }),

  advanceStep: (sessionId, chosenOptionNextStepId) =>
    request('/sessions/advance', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        chosen_option_next_step_id: chosenOptionNextStepId || null,
      }),
    }),

  endSession: (sessionId) =>
    request(`/sessions/${sessionId}/end`, { method: 'POST' }),

  chat: (sessionId, processId, question, profile) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        process_id: processId,
        question,
        agent_id: profile?.agentId || null,
        agent_name: profile?.name || null,
      }),
    }),

  flagAnswer: ({ sessionId, processId, question, answer, profile }) =>
    request('/feedback/flag', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId || null,
        process_id: processId || null,
        agent_id: profile?.agentId || null,
        agent_name: profile?.name || null,
        question,
        answer,
      }),
    }),

  // Supervisor / admin
  adminSessions: () => request('/admin/sessions'),
  adminQuestions: () => request('/admin/questions'),
  adminFlagged: () => request('/admin/flagged'),
}
