import { beforeEach, describe, expect, it, vi } from 'vitest'

import { slugify } from '../utils/format'
import { DEFAULT_APP_NAME } from './brandingDefaults'

async function loadBranding() {
  return import('./branding')
}

describe('branding', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('should fall back to the default name when no name is configured', async () => {
    vi.stubEnv('VITE_APP_NAME', '')
    vi.stubEnv('VITE_APP_SLUG', '')

    const { branding, storageKey } = await loadBranding()

    const defaultSlug = slugify(DEFAULT_APP_NAME)
    expect(defaultSlug).not.toBe('')
    expect(branding).toEqual({ name: DEFAULT_APP_NAME, slug: defaultSlug })
    expect(storageKey('session')).toBe(`${defaultSlug}:session`)
  })

  it('should derive the slug from the configured name', async () => {
    vi.stubEnv('VITE_APP_NAME', '  Acme Draw  ')
    vi.stubEnv('VITE_APP_SLUG', '')

    const { branding, storageKey } = await loadBranding()

    expect(branding).toEqual({ name: 'Acme Draw', slug: 'acme-draw' })
    expect(storageKey('theme')).toBe('acme-draw:theme')
  })

  it('should strip accents when deriving the slug', async () => {
    vi.stubEnv('VITE_APP_NAME', 'Diagramação Ágil')
    vi.stubEnv('VITE_APP_SLUG', '')

    const { branding } = await loadBranding()

    expect(branding.slug).toBe('diagramacao-agil')
  })

  it('should prefer an explicit slug over the derived one', async () => {
    vi.stubEnv('VITE_APP_NAME', 'Acme Draw')
    vi.stubEnv('VITE_APP_SLUG', ' legacy ')

    const { branding, storageKey } = await loadBranding()

    expect(branding.slug).toBe('legacy')
    expect(storageKey('pending-login')).toBe('legacy:pending-login')
  })

  it('should fall back to "app" when the name has no sluggable characters', async () => {
    vi.stubEnv('VITE_APP_NAME', '✨✨')
    vi.stubEnv('VITE_APP_SLUG', '')

    const { branding } = await loadBranding()

    expect(branding).toEqual({ name: '✨✨', slug: 'app' })
  })
})
