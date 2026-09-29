import { useId } from 'react'

import { branding } from '../../config/branding'

interface LogoProps {
  size?: number
  withWordmark?: boolean
}

// Product mark: two blocks joined by an elbow connector. Keep in sync with public/favicon.svg.
export default function Logo({ size = 24, withWordmark = false }: LogoProps) {
  const gradientId = useId()
  return (
    <span className="logo">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden={withWordmark} role={withWordmark ? undefined : 'img'} aria-label={withWordmark ? undefined : branding.name}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#5b5bd6" />
            <stop offset="1" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="8" fill={`url(#${gradientId})`} />
        <rect x="5.5" y="6" width="12.5" height="8.5" rx="2.5" fill="none" stroke="#fff" strokeWidth="2.2" />
        <rect x="16" y="17.5" width="10.5" height="8.5" rx="2.5" fill="#fff" />
        <path
          d="M11.75 14.5V21.75H16"
          fill="none"
          stroke="#fff"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {withWordmark ? <span className="logo-wordmark">{branding.name}</span> : null}
    </span>
  )
}
