// AgeCX AI mark: a soundwave inside a gradient tile (nods to live voice calls).
export default function Logo({ size = 38 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg width={size} height={size} viewBox="0 0 36 36" fill="none">
        <defs>
          <linearGradient id="agecx-grad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
            <stop stopColor="#6366f1" />
            <stop offset="1" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        <rect width="36" height="36" rx="10" fill="url(#agecx-grad)" />
        <g fill="#fff">
          <rect x="9.5" y="14" width="3" height="8" rx="1.5" />
          <rect x="15" y="10" width="3" height="16" rx="1.5" />
          <rect x="20.5" y="7" width="3" height="22" rx="1.5" />
          <rect x="26" y="13" width="3" height="10" rx="1.5" />
        </g>
      </svg>
    </span>
  )
}
