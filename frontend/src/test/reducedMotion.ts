import { vi } from 'vitest'

export interface FakeReducedMotion {
  setReduced: (reduced: boolean) => void
}

// jsdom has no matchMedia; this one answers the prefers-reduced-motion query and fires `change`.
export function stubReducedMotion(initiallyReduced: boolean): FakeReducedMotion {
  const listeners = new Set<() => void>()
  const query = {
    matches: initiallyReduced,
    media: '(prefers-reduced-motion: reduce)',
    addEventListener: (_type: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_type: string, listener: () => void) => listeners.delete(listener),
  }
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => query),
  )
  return {
    setReduced: (reduced) => {
      query.matches = reduced
      listeners.forEach((listener) => listener())
    },
  }
}
