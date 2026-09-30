import { vi } from 'vitest'

export interface FakeMediaQuery {
  setMatches: (matches: boolean) => void
}

// jsdom has no matchMedia; this one lets a test flip the OS colour scheme and fire `change`.
export function stubMatchMedia(initialMatches: boolean): FakeMediaQuery {
  const listeners = new Set<() => void>()
  const query = {
    matches: initialMatches,
    media: '(prefers-color-scheme: dark)',
    addEventListener: (_type: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_type: string, listener: () => void) => listeners.delete(listener),
  }
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => query),
  )
  return {
    setMatches: (matches) => {
      query.matches = matches
      listeners.forEach((listener) => listener())
    },
  }
}
