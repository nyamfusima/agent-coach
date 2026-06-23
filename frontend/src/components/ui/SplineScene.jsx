import { Component, Suspense, lazy } from 'react'
import Spinner from '../Spinner'

const Spline = lazy(() => import('@splinetool/react-spline'))

// If the 3D runtime or scene fails to load (offline, blocked CDN, WebGL off),
// fall back gracefully instead of crashing the landing page.
class SceneBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    if (this.state.failed) return this.props.fallback ?? null
    return this.props.children
  }
}

export function SplineScene({ scene, className }) {
  return (
    <SceneBoundary fallback={<div className="spline-fallback" aria-hidden="true" />}>
      <Suspense
        fallback={
          <div className="spline-loader">
            <Spinner size={26} label="Loading 3D scene…" />
          </div>
        }
      >
        <Spline scene={scene} className={className} />
      </Suspense>
    </SceneBoundary>
  )
}
