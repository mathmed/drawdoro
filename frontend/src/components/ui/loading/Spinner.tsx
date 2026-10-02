interface SpinnerProps {
  size?: number
  className?: string
}

// Inline spinner for pending buttons and small areas; the caller marks the busy element with aria-busy.
export default function Spinner({ size = 14, className }: SpinnerProps) {
  return (
    <svg
      className={className === undefined ? 'spinner-ring' : `spinner-ring ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      data-testid="spinner"
    >
      <circle className="spinner-ring-track" cx="12" cy="12" r="9" strokeWidth="2.5" />
      <path className="spinner-ring-arc" d="M21 12a9 9 0 0 0-9-9" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}
