import { useDelayedVisibility } from '../../../hooks/useDelayedVisibility'
import { usePresence } from '../../../hooks/usePresence'

const EXIT_MS = 240

interface TopProgressBarProps {
  active: boolean
  label: string
}

// Thin indeterminate bar along the top of its positioned parent, for work that keeps the current
// content on screen (switching diagrams, refreshing a project).
export default function TopProgressBar({ active, label }: TopProgressBarProps) {
  const visible = useDelayedVisibility(active, { delayMs: 120, minVisibleMs: 300 })
  const { isMounted, isExiting } = usePresence(visible, EXIT_MS)
  if (!isMounted) {
    return null
  }
  return (
    <div className="top-progress" data-state={isExiting ? 'exit' : 'enter'} role="progressbar" aria-label={label}>
      <span className="top-progress-bar" />
    </div>
  )
}
