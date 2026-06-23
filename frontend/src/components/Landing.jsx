import { useRef } from 'react'
import { SplineScene } from './ui/SplineScene'
import Logo from './Logo'

// The robot scene follows the cursor on its own; we add a spotlight glow that
// tracks the mouse for the hover animation.
const ROBOT_SCENE = 'https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode'

export default function Landing({ onGetStarted }) {
  const rootRef = useRef(null)

  const handleMove = (e) => {
    const el = rootRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty('--mx', `${e.clientX - rect.left}px`)
    el.style.setProperty('--my', `${e.clientY - rect.top}px`)
  }

  return (
    <div className="landing" ref={rootRef} onMouseMove={handleMove}>
      <div className="spotlight" aria-hidden="true" />

      <nav className="landing-nav">
        <div className="brand brand-on-dark">
          <Logo size={34} />
          <span className="brand-name">
            Age<span className="brand-accent">CX</span> <span className="brand-ai">AI</span>
          </span>
        </div>
        <button className="link link-on-dark" onClick={onGetStarted}>
          Sign in
        </button>
      </nav>

      <div className="landing-hero">
        <div className="landing-content">
          <span className="landing-eyebrow">AGECX AI</span>
          <h1 className="landing-title">
            The right answer,
            <br />
            the moment you need it.
          </h1>
          <p className="landing-sub">
            Your AI customer experience coach rides along on every call. It guides agents
            step by step and answers any policy question instantly, grounded in your real
            process docs. No holds, no hunting through manuals.
          </p>
          <div className="landing-actions">
            <button className="cta" onClick={onGetStarted}>
              Get started
            </button>
            <span className="landing-metrics">Higher FCR. Better NPS. Faster calls.</span>
          </div>
        </div>

        <div className="landing-robot">
          <SplineScene scene={ROBOT_SCENE} className="spline-canvas" />
        </div>
      </div>
    </div>
  )
}
