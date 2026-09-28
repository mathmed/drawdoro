import { create } from 'zustand'

import { authConfig } from '../auth/config'
import { clearSession, getIdToken, profileFromToken, type TokenProfile } from '../auth/session'

export type AuthStatus = 'loading' | 'signed-in' | 'signed-out'

interface AuthState {
  status: AuthStatus
  profile: TokenProfile | null
  initialize: () => Promise<void>
  signOutLocally: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  status: authConfig.enabled ? 'loading' : 'signed-in',
  profile: null,

  initialize: async () => {
    if (!authConfig.enabled) {
      set({ status: 'signed-in', profile: null })
      return
    }
    const token = await getIdToken()
    set(token === null ? { status: 'signed-out', profile: null } : { status: 'signed-in', profile: profileFromToken(token) })
  },

  // Used when the API rejects the session (revoked, user removed from the pool...).
  signOutLocally: () => {
    clearSession()
    set({ status: 'signed-out', profile: null })
  },
}))
