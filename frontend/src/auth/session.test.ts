import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'

import { fakeJwt } from '../test/jwt'

const DOMAIN = 'https://auth.example.com'
const CLIENT_ID = 'client-123'
const SESSION_KEY = 'test-app:session'
const PENDING_KEY = 'test-app:pending-login'
const NOW = new Date('2026-01-01T12:00:00Z').getTime()

interface StoredSession {
  idToken: string
  refreshToken: string
  expiresAt: number
}

let assign: Mock<(url: string) => void>
let fetchMock: Mock<typeof fetch>

function storeSession(session: StoredSession): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

function storedSession(): StoredSession | null {
  const raw = localStorage.getItem(SESSION_KEY)
  return raw === null ? null : (JSON.parse(raw) as StoredSession)
}

function tokenResponse(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function sentBody(call = 0): URLSearchParams {
  const init = fetchMock.mock.calls[call][1] as RequestInit
  return init.body as URLSearchParams
}

async function loadSession() {
  return import('./session')
}

async function sha256Base64Url(value: string): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))
  return btoa(String.fromCharCode(...digest)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

beforeEach(() => {
  vi.resetModules()
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(NOW)
  vi.stubEnv('VITE_COGNITO_DOMAIN', `${DOMAIN}/`)
  vi.stubEnv('VITE_COGNITO_CLIENT_ID', CLIENT_ID)
  vi.stubEnv('VITE_COGNITO_IDENTITY_PROVIDER', 'Google')
  assign = vi.fn()
  vi.stubGlobal('location', { ...window.location, origin: 'http://localhost:3000', assign })
  fetchMock = vi.fn<typeof fetch>()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('decodeJwt', () => {
  it('should decode a base64url payload with non-ASCII characters', async () => {
    const { decodeJwt } = await loadSession()

    const claims = decodeJwt(fakeJwt({ name: 'João Ção', sub: '1?>~' }))

    expect(claims).toEqual({ name: 'João Ção', sub: '1?>~' })
  })
})

describe('profileFromToken', () => {
  it('should read email, name and picture from the token', async () => {
    const { profileFromToken } = await loadSession()

    const profile = profileFromToken(fakeJwt({ email: 'ana@example.com', name: 'Ana', picture: 'https://pic' }))

    expect(profile).toEqual({ email: 'ana@example.com', name: 'Ana', picture: 'https://pic' })
  })

  it('should fall back to the email local part when the name is missing', async () => {
    const { profileFromToken } = await loadSession()

    const profile = profileFromToken(fakeJwt({ email: 'bruno.silva@example.com', name: '', picture: 42 }))

    expect(profile).toEqual({ email: 'bruno.silva@example.com', name: 'bruno.silva', picture: undefined })
  })
})

describe('session storage', () => {
  it('should start signed out when nothing is stored', async () => {
    const { getIdToken, hasSession } = await loadSession()

    expect(hasSession()).toBe(false)
    await expect(getIdToken()).resolves.toBeNull()
  })

  it('should ignore a corrupted stored session', async () => {
    localStorage.setItem(SESSION_KEY, '{not json')

    const { hasSession } = await loadSession()

    expect(hasSession()).toBe(false)
  })

  it('should only read the session stored under the branding slug', async () => {
    localStorage.setItem('other:session', JSON.stringify({ idToken: 'x', refreshToken: 'y', expiresAt: NOW + 3_600_000 }))

    const { hasSession } = await loadSession()

    expect(hasSession()).toBe(false)
  })

  it('should return the stored token while it is valid beyond the safety margin', async () => {
    storeSession({ idToken: 'id-1', refreshToken: 'refresh-1', expiresAt: NOW + 61_000 })

    const { getIdToken, hasSession } = await loadSession()

    expect(hasSession()).toBe(true)
    await expect(getIdToken()).resolves.toBe('id-1')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('should clear the session from memory and storage', async () => {
    storeSession({ idToken: 'id-1', refreshToken: 'refresh-1', expiresAt: NOW + 3_600_000 })
    const { clearSession, hasSession } = await loadSession()

    clearSession()

    expect(hasSession()).toBe(false)
    expect(storedSession()).toBeNull()
  })
})

describe('getIdToken refresh', () => {
  it('should refresh a token that expires within the safety margin', async () => {
    storeSession({ idToken: 'old', refreshToken: 'refresh-1', expiresAt: NOW + 59_000 })
    fetchMock.mockResolvedValue(tokenResponse({ id_token: 'new', expires_in: 3600 }))
    const { getIdToken } = await loadSession()

    const token = await getIdToken()

    expect(token).toBe('new')
    expect(fetchMock).toHaveBeenCalledWith(`${DOMAIN}/oauth2/token`, expect.objectContaining({ method: 'POST' }))
    expect(Object.fromEntries(sentBody())).toEqual({
      client_id: CLIENT_ID,
      grant_type: 'refresh_token',
      refresh_token: 'refresh-1',
    })
    expect(storedSession()).toEqual({ idToken: 'new', refreshToken: 'refresh-1', expiresAt: NOW + 3_600_000 })
  })

  it('should keep a rotated refresh token', async () => {
    storeSession({ idToken: 'old', refreshToken: 'refresh-1', expiresAt: NOW - 1 })
    fetchMock.mockResolvedValue(tokenResponse({ id_token: 'new', refresh_token: 'refresh-2', expires_in: 60 }))
    const { getIdToken } = await loadSession()

    await getIdToken()

    expect(storedSession()?.refreshToken).toBe('refresh-2')
  })

  it('should share a single refresh request between concurrent callers', async () => {
    storeSession({ idToken: 'old', refreshToken: 'refresh-1', expiresAt: NOW - 1 })
    fetchMock.mockResolvedValue(tokenResponse({ id_token: 'new', expires_in: 3600 }))
    const { getIdToken } = await loadSession()

    const tokens = await Promise.all([getIdToken(), getIdToken(), getIdToken()])

    expect(tokens).toEqual(['new', 'new', 'new'])
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('should sign out when the refresh is rejected', async () => {
    storeSession({ idToken: 'old', refreshToken: 'revoked', expiresAt: NOW - 1 })
    fetchMock.mockResolvedValue(tokenResponse({ error: 'invalid_grant' }, 400))
    const { getIdToken, hasSession } = await loadSession()

    await expect(getIdToken()).resolves.toBeNull()

    expect(hasSession()).toBe(false)
    expect(storedSession()).toBeNull()
  })

  it('should sign out when the token endpoint is unreachable', async () => {
    storeSession({ idToken: 'old', refreshToken: 'refresh-1', expiresAt: NOW - 1 })
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))
    const { getIdToken, hasSession } = await loadSession()

    await expect(getIdToken()).resolves.toBeNull()

    expect(hasSession()).toBe(false)
  })

  it('should retry on a later call after a refresh finished', async () => {
    storeSession({ idToken: 'old', refreshToken: 'refresh-1', expiresAt: NOW - 1 })
    fetchMock.mockResolvedValue(tokenResponse({ id_token: 'short', expires_in: 30 }))
    const { getIdToken } = await loadSession()

    await getIdToken()
    fetchMock.mockResolvedValue(tokenResponse({ id_token: 'fresh', expires_in: 3600 }))

    await expect(getIdToken()).resolves.toBe('fresh')
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})

describe('startLogin', () => {
  it('should store the pending login and redirect to the PKCE authorize URL', async () => {
    const { startLogin } = await loadSession()

    await startLogin('/diagrams/42?tab=docs')

    const pending = JSON.parse(sessionStorage.getItem(PENDING_KEY) ?? 'null') as Record<string, string>
    expect(pending.returnTo).toBe('/diagrams/42?tab=docs')
    expect(new Set([pending.state, pending.nonce, pending.verifier]).size).toBe(3)
    expect(pending.verifier).toMatch(/^[A-Za-z0-9_-]{43}$/)

    const url = new URL(assign.mock.calls[0][0])
    expect(`${url.origin}${url.pathname}`).toBe(`${DOMAIN}/oauth2/authorize`)
    expect(Object.fromEntries(url.searchParams)).toEqual({
      response_type: 'code',
      client_id: CLIENT_ID,
      redirect_uri: 'http://localhost:3000/auth/callback',
      scope: 'openid email profile',
      state: pending.state,
      nonce: pending.nonce,
      code_challenge: await sha256Base64Url(pending.verifier),
      code_challenge_method: 'S256',
      identity_provider: 'Google',
    })
  })

  it('should omit the identity provider when it is configured empty', async () => {
    vi.stubEnv('VITE_COGNITO_IDENTITY_PROVIDER', '')
    const { startLogin } = await loadSession()

    await startLogin('/')

    expect(new URL(assign.mock.calls[0][0]).searchParams.has('identity_provider')).toBe(false)
  })
})

describe('completeLogin', () => {
  function storePending(pending: Record<string, string>): void {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(pending))
  }

  const pending = { state: 'state-1', nonce: 'nonce-1', verifier: 'verifier-1', returnTo: '/projects' }

  it('should exchange the code, save the session and return the original path', async () => {
    storePending(pending)
    fetchMock.mockResolvedValue(
      tokenResponse({ id_token: fakeJwt({ nonce: 'nonce-1' }), refresh_token: 'refresh-1', expires_in: 3600 }),
    )
    const { completeLogin, hasSession } = await loadSession()

    const returnTo = await completeLogin('?code=abc&state=state-1')

    expect(returnTo).toBe('/projects')
    expect(Object.fromEntries(sentBody())).toEqual({
      client_id: CLIENT_ID,
      grant_type: 'authorization_code',
      code: 'abc',
      redirect_uri: 'http://localhost:3000/auth/callback',
      code_verifier: 'verifier-1',
    })
    expect(hasSession()).toBe(true)
    expect(storedSession()?.refreshToken).toBe('refresh-1')
    expect(sessionStorage.getItem(PENDING_KEY)).toBeNull()
  })

  it('should surface the error returned by the identity provider', async () => {
    const { completeLogin } = await loadSession()

    await expect(completeLogin('?error=access_denied&error_description=User+cancelled')).rejects.toThrow(
      'User cancelled',
    )
  })

  it('should reject a response whose state does not match and discard the pending login', async () => {
    storePending(pending)
    const { completeLogin } = await loadSession()

    await expect(completeLogin('?code=abc&state=forged')).rejects.toThrow('The sign-in attempt expired')

    expect(sessionStorage.getItem(PENDING_KEY)).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('should reject a callback without a pending login', async () => {
    const { completeLogin } = await loadSession()

    await expect(completeLogin('?code=abc&state=state-1')).rejects.toThrow('The sign-in attempt expired')
  })

  it('should reject a token whose nonce does not match', async () => {
    storePending(pending)
    fetchMock.mockResolvedValue(tokenResponse({ id_token: fakeJwt({ nonce: 'other' }), expires_in: 3600 }))
    const { completeLogin, hasSession } = await loadSession()

    await expect(completeLogin('?code=abc&state=state-1')).rejects.toThrow('could not be verified')

    expect(hasSession()).toBe(false)
  })
})

describe('logout', () => {
  it('should clear the session and redirect to the hosted logout', async () => {
    storeSession({ idToken: 'id-1', refreshToken: 'refresh-1', expiresAt: NOW + 3_600_000 })
    const { hasSession, logout } = await loadSession()

    logout()

    expect(hasSession()).toBe(false)
    expect(storedSession()).toBeNull()
    const url = new URL(assign.mock.calls[0][0])
    expect(`${url.origin}${url.pathname}`).toBe(`${DOMAIN}/logout`)
    expect(Object.fromEntries(url.searchParams)).toEqual({ client_id: CLIENT_ID, logout_uri: 'http://localhost:3000' })
  })
})
