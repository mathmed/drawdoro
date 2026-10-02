import { useSyncExternalStore } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

function mediaQuery(): MediaQueryList | null {
  return typeof window.matchMedia === 'function' ? window.matchMedia(QUERY) : null
}

function subscribe(onChange: () => void): () => void {
  const query = mediaQuery()
  query?.addEventListener('change', onChange)
  return () => query?.removeEventListener('change', onChange)
}

function prefersReducedMotion(): boolean {
  return mediaQuery()?.matches ?? false
}

export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, prefersReducedMotion, () => false)
}
