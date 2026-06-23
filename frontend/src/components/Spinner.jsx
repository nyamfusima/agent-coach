export default function Spinner({ size = 16, label }) {
  return (
    <span className="spinner-wrap">
      <span
        className="spinner"
        style={{ width: size, height: size }}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && <span className="spinner-label">{label}</span>}
    </span>
  )
}
