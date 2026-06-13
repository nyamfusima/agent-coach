import { useState } from 'react'
import ProcessSelector from './components/ProcessSelector'
import FlowPanel from './components/FlowPanel'
import ChatPanel from './components/ChatPanel'
import { api } from './api'

export default function App() {
  const [session, setSession] = useState(null)
  const [error, setError] = useState(null)

  const handleStart = async (agentId, processId) => {
    setError(null)
    try {
      const result = await api.startSession(agentId, processId)
      setSession(result)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="app">
      <header>
        <div className="header-titles">
          <h1>Agent Coach</h1>
          <p className="subtitle">Live call guidance &amp; process Q&amp;A</p>
        </div>
        {session && (
          <button className="link" onClick={() => setSession(null)}>
            End call / start new
          </button>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      {!session ? (
        <ProcessSelector onStart={handleStart} />
      ) : (
        <div className="layout">
          <FlowPanel session={session} setSession={setSession} />
          <ChatPanel session={session} />
        </div>
      )}
    </div>
  )
}
