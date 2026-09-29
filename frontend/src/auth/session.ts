import { storageKey } from '../config/branding'
import { authConfig } from './config'

interface Session {
  idToken: string
  refreshToken: string
  expiresAt: number
}

interface PendingLogin {
  state: string
  nonce: string
  verifier: string
  returnTo: string
}

export interface TokenProfile {
  email: string
  name: string
  picture?: string
}

const SESSION_KEY = storageKey('session')
const PENDING_KEY = storageKey('pending-login')
// Refresh a minute early so requests never race the expiry.
const EXPIRY_MARGIN_MS = 60_000

function base64Url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function randomString(): string {
  return base64Url(crypto.getRandomValues(new Uint8Array(32)))
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return base64Url(new Uint8Array(digest))
}

function readJson<T>(storage: Storage, key: string): T | null {
  try {
    const raw = storage.getItem(key)
    return raw === null ? null : (JSON.parse(raw) as T)
  } catch {
    return null
  }
}

function writeJson(storage: Storage, key: string, value: unknown): void {
  try {
    storage.setItem(key, JSON.stringify(value))
  } catch {
    // Storage can be unavailable (private mode); the session then lasts for this page only.
  }
}

function removeKey(storage: Storage, key: string): void {
  try {
    storage.removeItem(key)
  } catch {
    // Nothing to clean up when storage is unavailable.
  }
}

export function decodeJwt(token: string): Record<string, unknown> {
  const payload = token.split('.')[1] ?? ''
  const bytes = Uint8Array.from(atob(payload.replace(/-/g, '+').replace(/_/g, '/')), (char) => char.charCodeAt(0))
  return JSON.parse(new TextDecoder().decode(bytes)) as Record<string, unknown>
}

export function profileFromToken(idToken: string): TokenProfile {
  const claims = decodeJwt(idToken)
  const email = String(claims.email ?? '')
  const name = typeof claims.name === 'string' && claims.name !== '' ? claims.name : email.split('@')[0]
  return { email, name, picture: typeof claims.picture === 'string' ? claims.picture : undefined }
}

let memorySession: Session | null = readJson<Session>(localStorage, SESSION_KEY)
let refreshing: Promise<string | null> | null = null

function saveSession(session: Session | null): void {
  memorySession = session
  if (session === null) {
    removeKey(localStorage, SESSION_KEY)
  } else {
    writeJson(localStorage, SESSION_KEY, session)
  }
}

async function requestTokens(body: Record<string, string>): Promise<Session> {
  const response = await fetch(`${authConfig.domain}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: authConfig.clientId, ...body }),
  })
  if (!response.ok) {
    throw new Error(`Token request failed (${response.status})`)
  }
  const data = (await response.json()) as { id_token: string; refresh_token?: string; expires_in: number }
  return {
    idToken: data.id_token,
    // Refresh responses don't return a new refresh token unless rotation is enabled.
    refreshToken: data.refresh_token ?? body.refresh_token ?? '',
    expiresAt: Date.now() + data.expires_in * 1000,
  }
}

export function hasSession(): boolean {
  return memorySession !== null
}

// Returns a valid ID token, refreshing it when it is about to expire; null means signed out.
export async function getIdToken(): Promise<string | null> {
  const session = memorySession
  if (session === null) {
    return null
  }
  if (session.expiresAt - EXPIRY_MARGIN_MS > Date.now()) {
    return session.idToken
  }
  if (refreshing === null) {
    refreshing = requestTokens({ grant_type: 'refresh_token', refresh_token: session.refreshToken })
      .then((next) => {
        saveSession(next)
        return next.idToken
      })
      .catch(() => {
        saveSession(null)
        return null
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

export async function startLogin(returnTo: string): Promise<void> {
  const pending: PendingLogin = { state: randomString(), nonce: randomString(), verifier: randomString(), returnTo }
  writeJson(sessionStorage, PENDING_KEY, pending)
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: authConfig.clientId,
    redirect_uri: authConfig.redirectUri,
    scope: authConfig.scopes,
    state: pending.state,
    nonce: pending.nonce,
    code_challenge: await sha256(pending.verifier),
    code_challenge_method: 'S256',
  })
  if (authConfig.identityProvider !== '') {
    params.set('identity_provider', authConfig.identityProvider)
  }
  window.location.assign(`${authConfig.domain}/oauth2/authorize?${params.toString()}`)
}

// Finishes the redirect from Cognito and returns the path the user was trying to open.
export async function completeLogin(search: string): Promise<string> {
  const params = new URLSearchParams(search)
  const error = params.get('error_description') ?? params.get('error')
  if (error !== null) {
    throw new Error(error)
  }
  const pending = readJson<PendingLogin>(sessionStorage, PENDING_KEY)
  removeKey(sessionStorage, PENDING_KEY)
  const code = params.get('code')
  if (pending === null || code === null || params.get('state') !== pending.state) {
    throw new Error('The sign-in attempt expired. Please try again.')
  }
  const session = await requestTokens({
    grant_type: 'authorization_code',
    code,
    redirect_uri: authConfig.redirectUri,
    code_verifier: pending.verifier,
  })
  if (decodeJwt(session.idToken).nonce !== pending.nonce) {
    throw new Error('The sign-in response could not be verified. Please try again.')
  }
  saveSession(session)
  return pending.returnTo
}

export function logout(): void {
  saveSession(null)
  const params = new URLSearchParams({ client_id: authConfig.clientId, logout_uri: authConfig.logoutUri })
  window.location.assign(`${authConfig.domain}/logout?${params.toString()}`)
}

export function clearSession(): void {
  saveSession(null)
}
