import type { CSSProperties, ReactNode } from 'react'

interface SkeletonProps {
  width?: CSSProperties['width']
  height?: CSSProperties['height']
  radius?: CSSProperties['borderRadius']
  className?: string
}

// A placeholder block with a soft shimmer, sized like the content it stands in for.
export function Skeleton({ width, height, radius, className }: SkeletonProps) {
  return (
    <span
      className={className === undefined ? 'skeleton' : `skeleton ${className}`}
      style={{ width, height, borderRadius: radius }}
      aria-hidden="true"
    />
  )
}

interface SkeletonGroupProps {
  // Announced to assistive tech instead of the decorative blocks.
  label: string
  className?: string
  children: ReactNode
}

export function SkeletonGroup({ label, className, children }: SkeletonGroupProps) {
  return (
    <div className={className === undefined ? 'skeleton-group' : `skeleton-group ${className}`} role="status">
      <span className="sr-only">{label}</span>
      <div className="skeleton-group-body" aria-hidden="true">
        {children}
      </div>
    </div>
  )
}

const LINE_WIDTHS = ['72%', '48%', '60%', '36%']

interface ListSkeletonProps {
  label: string
  rows?: number
  lines?: number
  avatar?: 'circle' | 'square' | 'none'
  className?: string
}

// Rows of an avatar and a few text lines: history entries, comments, keys, members.
export function ListSkeleton({ label, rows = 4, lines = 2, avatar = 'circle', className }: ListSkeletonProps) {
  return (
    <SkeletonGroup label={label} className={className === undefined ? 'list-skeleton' : `list-skeleton ${className}`}>
      {Array.from({ length: rows }, (_, row) => (
        <div key={row} className="list-skeleton-row">
          {avatar === 'none' ? null : (
            <Skeleton className="list-skeleton-avatar" radius={avatar === 'circle' ? '50%' : 'var(--radius-sm)'} />
          )}
          <div className="list-skeleton-lines">
            {Array.from({ length: lines }, (_, line) => (
              <Skeleton
                key={line}
                className="skeleton-line"
                width={LINE_WIDTHS[(row + line) % LINE_WIDTHS.length]}
                height={line === 0 ? 11 : 9}
              />
            ))}
          </div>
        </div>
      ))}
    </SkeletonGroup>
  )
}
