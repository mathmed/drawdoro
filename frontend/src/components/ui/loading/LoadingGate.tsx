import type { ReactNode } from 'react'

import { useDelayedVisibility, type DelayedVisibilityOptions } from '../../../hooks/useDelayedVisibility'

interface LoadingGateProps extends DelayedVisibilityOptions {
  loading: boolean
  fallback: ReactNode
  // Drawn during the appear delay, e.g. to reserve the room the content will take.
  placeholder?: ReactNode
  // A function when the content cannot even be built until the data arrives.
  children: ReactNode | (() => ReactNode)
}

// Swaps content for a loader without flashing it on fast loads: only the placeholder is drawn for
// the first moments, and a loader that did appear stays up long enough to be read.
export default function LoadingGate({ loading, fallback, placeholder = null, children, delayMs, minVisibleMs }: LoadingGateProps) {
  const showFallback = useDelayedVisibility(loading, { delayMs, minVisibleMs })
  if (showFallback) {
    return <>{fallback}</>
  }
  if (loading) {
    return <>{placeholder}</>
  }
  return <>{typeof children === 'function' ? children() : children}</>
}
