import { RotateCw } from 'lucide-react'
import { useEffect, useState, type CSSProperties } from 'react'

import { branding } from '../../../config/branding'
import { usePrefersReducedMotion } from '../../../hooks/usePrefersReducedMotion'
import Logo from '../Logo'
import { registerBrandLoader } from './brandLoaderRegistry'

export const SLOW_LOAD_MS = 8000
const DEFAULT_SLOW_HINT = 'This is taking longer than usual.'

interface BrandLoaderProps {
  label: string
  // Shown under the label once the wait passes `slowAfterMs`, with the retry action if there is one.
  slowHint?: string
  slowAfterMs?: number
  onRetry?: () => void
  retryLabel?: string
  showName?: boolean
  size?: number
}

// Full-area loader built on the product logo, so a white-label build shows its own mark and name.
export default function BrandLoader({
  label,
  slowHint = DEFAULT_SLOW_HINT,
  slowAfterMs = SLOW_LOAD_MS,
  onRetry,
  retryLabel = 'Try again',
  showName = false,
  size = 44,
}: BrandLoaderProps) {
  const reducedMotion = usePrefersReducedMotion()
  const [isSlow, setIsSlow] = useState(false)

  useEffect(() => registerBrandLoader(), [])

  useEffect(() => {
    const timer = setTimeout(() => setIsSlow(true), slowAfterMs)
    return () => clearTimeout(timer)
  }, [slowAfterMs])

  const style = { '--brand-loader-size': `${size}px` } as CSSProperties

  return (
    <div className="brand-loader" data-motion={reducedMotion ? 'reduced' : 'full'} style={style}>
      <div className="brand-loader-mark" aria-hidden="true">
        <span className="brand-loader-halo" />
        <svg className="brand-loader-orbit" viewBox="0 0 100 100">
          <circle className="brand-loader-orbit-track" cx="50" cy="50" r="47" />
          <circle className="brand-loader-orbit-arc" cx="50" cy="50" r="47" pathLength="100" />
        </svg>
        <span className="brand-loader-logo">
          <Logo size={size} />
        </span>
      </div>
      {showName ? (
        <div className="brand-loader-name" aria-hidden="true">
          {branding.name}
        </div>
      ) : null}
      <div className="brand-loader-text" role="status" aria-live="polite">
        <span className="sr-only">{branding.name}: </span>
        <span className="brand-loader-label">
          {label}
          <span className="brand-loader-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </span>
        {isSlow ? <span className="brand-loader-hint">{slowHint}</span> : null}
      </div>
      {isSlow && onRetry !== undefined ? (
        <button type="button" className="btn btn-secondary btn-sm brand-loader-retry" onClick={onRetry}>
          <RotateCw size={13} /> {retryLabel}
        </button>
      ) : null}
    </div>
  )
}
