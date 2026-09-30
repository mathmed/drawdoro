import { beforeEach, describe, expect, it, vi } from 'vitest'

import { stubMatchMedia } from '../test/matchMedia'

const THEME_KEY = 'test-app:theme'

async function loadStore() {
  const { useThemeStore } = await import('./useThemeStore')
  return useThemeStore
}

describe('useThemeStore', () => {
  beforeEach(() => {
    vi.resetModules()
    delete document.documentElement.dataset.theme
  })

  it('should follow the system theme when nothing is stored', async () => {
    stubMatchMedia(true)

    const store = await loadStore()

    expect(store.getState()).toMatchObject({ preference: 'system', resolved: 'dark' })
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('should restore the stored preference', async () => {
    stubMatchMedia(true)
    localStorage.setItem(THEME_KEY, 'light')

    const store = await loadStore()

    expect(store.getState()).toMatchObject({ preference: 'light', resolved: 'light' })
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('should ignore an unknown stored value', async () => {
    stubMatchMedia(false)
    localStorage.setItem(THEME_KEY, 'sepia')

    const store = await loadStore()

    expect(store.getState()).toMatchObject({ preference: 'system', resolved: 'light' })
  })

  it('should fall back to the system theme when storage is unavailable', async () => {
    stubMatchMedia(true)
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('denied', 'SecurityError')
    })

    const store = await loadStore()

    expect(store.getState().preference).toBe('system')
  })

  it('should persist and apply a new preference', async () => {
    stubMatchMedia(false)
    const store = await loadStore()

    store.getState().setPreference('dark')

    expect(store.getState()).toMatchObject({ preference: 'dark', resolved: 'dark' })
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('should still apply the preference when storage rejects the write', async () => {
    stubMatchMedia(false)
    const store = await loadStore()
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota', 'QuotaExceededError')
    })

    store.getState().setPreference('dark')

    expect(store.getState().resolved).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('should react to OS theme changes while following the system', async () => {
    const media = stubMatchMedia(false)
    const store = await loadStore()

    media.setMatches(true)

    expect(store.getState().resolved).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('should ignore OS theme changes when a theme was chosen explicitly', async () => {
    const media = stubMatchMedia(false)
    const store = await loadStore()
    store.getState().setPreference('light')

    media.setMatches(true)

    expect(store.getState().resolved).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')
  })
})
