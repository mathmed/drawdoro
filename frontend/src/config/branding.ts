import { slugify } from '../utils/format'
import { DEFAULT_APP_NAME } from './brandingDefaults'

const name = import.meta.env.VITE_APP_NAME?.trim() || DEFAULT_APP_NAME
// Prefixes browser storage keys, so changing it signs everyone out and forgets their preferences.
const slug = import.meta.env.VITE_APP_SLUG?.trim() || slugify(name) || 'app'

export const branding = { name, slug } as const

export function storageKey(key: string): string {
  return `${slug}:${key}`
}
