import type { ReactNode } from 'react'

import { usePresence } from '../../../hooks/usePresence'

export const OVERLAY_EXIT_MS = 220

interface LoadingOverlayProps {
  visible: boolean
  // Covers the whole viewport instead of the positioned parent.
  screen?: boolean
  children: ReactNode
}

// Covers an area while content loads underneath, then fades out to reveal it.
export default function LoadingOverlay({ visible, screen = false, children }: LoadingOverlayProps) {
  const { isMounted, isExiting } = usePresence(visible, OVERLAY_EXIT_MS)
  if (!isMounted) {
    return null
  }
  return (
    <div
      className={screen ? 'loading-overlay loading-overlay-screen' : 'loading-overlay'}
      data-state={isExiting ? 'exit' : 'enter'}
      aria-hidden={isExiting}
    >
      {children}
    </div>
  )
}
