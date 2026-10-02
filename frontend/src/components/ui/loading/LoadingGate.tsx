import type { ReactNode } from 'react'

import { useDelayedVisibility, type DelayedVisibilityOptions } from '../../../hooks/useDelayedVisibility'

interface LoadingGateProps extends DelayedVisibilityOptions {
  loading: boolean
  fallback: ReactNode
  // A function when the content cannot even be built until the data arrives.
  children: ReactNode | (() => ReactNode)
}

// Swaps content for a loader without flashing it on fast loads: nothing is drawn for the first
// moments, and a loader that did appear stays up long enough to be read.
export default function LoadingGate({ loading, fallback, children, delayMs, minVisibleMs }: LoadingGateProps) {
  const showFallback = useDelayedVisibility(loading, { delayMs, minVisibleMs })
  if (showFallback) {
    return <>{fallback}</>
  }
  if (loading) {
    return null
  }
  return <>{typeof children === 'function' ? children() : children}</>
}
