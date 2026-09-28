// Cognito managed login (Hosted UI). Leaving the domain or client id empty disables login,
// which is how local development runs against an API with AUTH_ENABLED=false.
const domain = (import.meta.env.VITE_COGNITO_DOMAIN ?? '').replace(/\/+$/, '')
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID ?? ''

export const authConfig = {
  enabled: domain !== '' && clientId !== '',
  domain,
  clientId,
  // Skips Cognito's provider picker and goes straight to Google.
  identityProvider: import.meta.env.VITE_COGNITO_IDENTITY_PROVIDER ?? 'Google',
  scopes: 'openid email profile',
  redirectUri: `${window.location.origin}/auth/callback`,
  // Registered sign-out URLs are matched exactly, so this is the bare origin (no trailing slash).
  logoutUri: window.location.origin,
}
