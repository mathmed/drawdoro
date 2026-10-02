import { useEffect, useRef, useState } from 'react'

// Waits shorter than this feel instant, so no loader is shown for them.
export const LOADER_DELAY_MS = 180
// Once shown, a loader stays at least this long so it never flickers in and out.
export const LOADER_MIN_VISIBLE_MS = 450

export interface DelayedVisibilityOptions {
  delayMs?: number
  minVisibleMs?: number
}

export function useDelayedVisibility(
  active: boolean,
  { delayMs = LOADER_DELAY_MS, minVisibleMs = LOADER_MIN_VISIBLE_MS }: DelayedVisibilityOptions = {},
): boolean {
  const [visible, setVisible] = useState(() => active && delayMs <= 0)
  const shownAt = useRef<number | null>(null)

  useEffect(() => {
    if (visible && shownAt.current === null) {
      shownAt.current = Date.now()
    }
    if (active && !visible) {
      const timer = setTimeout(() => {
        shownAt.current = Date.now()
        setVisible(true)
      }, delayMs)
      return () => clearTimeout(timer)
    }
    if (!active && visible) {
      const elapsed = Date.now() - (shownAt.current ?? 0)
      const timer = setTimeout(
        () => {
          shownAt.current = null
          setVisible(false)
        },
        Math.max(0, minVisibleMs - elapsed),
      )
      return () => clearTimeout(timer)
    }
    return undefined
  }, [active, visible, delayMs, minVisibleMs])

  return visible
}
