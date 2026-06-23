import { useState } from 'react'
import ProcessSelector from './components/ProcessSelector'
import FlowPanel from './components/FlowPanel'
import ChatPanel from './components/ChatPanel'
import Login from './components/Login'
import Landing from './components/Landing'
import Logo from './components/Logo'
import { api } from './api'
import { loadProfile, clearProfile } from './profile'

function Brand() {
  return (
    <div className="brand">
      <Logo />
      <div className="brand-text">
        <span className="brand-name">
          Age<span className="brand-accent">CX</span> <span className="brand-ai">AI</span>
        </span>
        <span className="brand-tag">Your agent customer experience coach AI</span>
      </div>
    </div>
  )
}

export default function App() {
  const [profile, setProfile] = useState(loadProfile())
  const [session, setSession] = useState(null)
  const [error, setError] = useState(null)
  const [showLogin, setShowLogin] = useState(false)

  // Pre-login: immersive landing hero. "Get started" reveals the sign-in form.
  if (!profile && !showLogin) {
    return <Landing onGetStarted={() => setShowLogin(true)} />
  }

  const handleStart = async (processId) => {
    setError(null)
    try {
      const result = await api.startSession(profile, processId)
      setSession(result)
    } catch (e) {
      setError(e.message)
    }
  }

  const endCall = async () => {
    if (session) {
      try {
        await api.endSession(session.session_id)
      } catch {
        /* non blocking, still let the agent move on */
      }
    }
    setSession(null)
  }

  const signOut = () => {
    clearProfile()
    setProfile(null)
    setSession(null)
  }

  return (
    <div className="app">
      <header className="topbar">
        <Brand />
        {profile && (
          <div className="header-actions">
            {session && <span className="calltype-chip">{session.process.name}</span>}
            <span className="agent-badge">
              {profile.name}
              {profile.team ? ` · ${profile.team}` : ''}
            </span>
            {session ? (
              <button className="link" onClick={endCall}>
                End call / start new
              </button>
            ) : (
              <button className="link" onClick={signOut}>
                Sign out
              </button>
            )}
          </div>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      {!profile ? (
        <Login onSave={setProfile} />
      ) : !session ? (
        <ProcessSelector onStart={handleStart} />
      ) : (
        <div className="layout">
          <FlowPanel session={session} setSession={setSession} />
          <ChatPanel session={session} profile={profile} />
        </div>
      )}
    </div>
  )
}
