import { useEffect, useState } from 'react'

export interface Presence {
  isMounted: boolean
  isExiting: boolean
}

// Keeps an element mounted for `exitMs` after it is hidden, so it can fade out instead of vanishing.
export function usePresence(visible: boolean, exitMs: number): Presence {
  const [lingering, setLingering] = useState(visible)
  if (visible && !lingering) {
    setLingering(true)
  }

  useEffect(() => {
    if (visible || !lingering) {
      return undefined
    }
    const timer = setTimeout(() => setLingering(false), exitMs)
    return () => clearTimeout(timer)
  }, [visible, lingering, exitMs])

  return { isMounted: visible || lingering, isExiting: !visible && lingering }
}
