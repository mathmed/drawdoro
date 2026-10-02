import { act } from '@testing-library/react'
import { vi } from 'vitest'

import { LOADER_DELAY_MS, LOADER_MIN_VISIBLE_MS } from '../hooks/useDelayedVisibility'

const STEP_MS = 10

// Moves fake timers forward in small steps, each in its own act(), so a timer that renders something
// which starts another timer (a loader appearing, then its exit) plays out as it would in a browser.
export async function advance(ms: number): Promise<void> {
  let remaining = ms
  do {
    const step = Math.min(STEP_MS, remaining)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(step)
    })
    remaining -= step
  } while (remaining > 0)
}

export function pastLoaderDelay(): Promise<void> {
  return advance(LOADER_DELAY_MS)
}

// Enough for a visible loader to reach its minimum time and finish fading out.
export function pastLoaderExit(): Promise<void> {
  return advance(LOADER_MIN_VISIBLE_MS + 300)
}
