import type { ReactNode } from 'react'

import { usePresence } from '../../../hooks/usePresence'

export const OVERLAY_EXIT_MS = 220

interface LoadingOverlayProps {
  visible: boolean
  children: ReactNode
}

// Covers its positioned parent while content loads underneath, then fades out to reveal it.
export default function LoadingOverlay({ visible, children }: LoadingOverlayProps) {
  const { isMounted, isExiting } = usePresence(visible, OVERLAY_EXIT_MS)
  if (!isMounted) {
    return null
  }
  return (
    <div className="loading-overlay" data-state={isExiting ? 'exit' : 'enter'} aria-hidden={isExiting}>
      {children}
    </div>
  )
}
