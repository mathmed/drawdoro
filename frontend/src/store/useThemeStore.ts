import { create } from 'zustand'

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'drawdoro:theme'
const darkQuery = window.matchMedia('(prefers-color-scheme: dark)')

function readPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored
    }
  } catch {
    // Storage can be unavailable (private mode); fall back to the system theme.
  }
  return 'system'
}

function resolve(preference: ThemePreference): ResolvedTheme {
  if (preference === 'system') {
    return darkQuery.matches ? 'dark' : 'light'
  }
  return preference
}

function apply(theme: ResolvedTheme): void {
  document.documentElement.dataset.theme = theme
}

interface ThemeState {
  preference: ThemePreference
  resolved: ResolvedTheme
  setPreference: (preference: ThemePreference) => void
}

const initialPreference = readPreference()

export const useThemeStore = create<ThemeState>((set) => ({
  preference: initialPreference,
  resolved: resolve(initialPreference),
  setPreference: (preference) => {
    try {
      localStorage.setItem(STORAGE_KEY, preference)
    } catch {
      // Not persisted; the choice still applies to this session.
    }
    const resolved = resolve(preference)
    apply(resolved)
    set({ preference, resolved })
  },
}))

apply(useThemeStore.getState().resolved)

darkQuery.addEventListener('change', () => {
  const { preference } = useThemeStore.getState()
  if (preference !== 'system') {
    return
  }
  const resolved = resolve(preference)
  apply(resolved)
  useThemeStore.setState({ resolved })
})
