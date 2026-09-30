function base64Url(value: string): string {
  const bytes = new TextEncoder().encode(value)
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

// Unsigned token: the frontend only decodes the payload, the API is the one that verifies it.
export function fakeJwt(claims: Record<string, unknown>): string {
  return `${base64Url(JSON.stringify({ alg: 'none' }))}.${base64Url(JSON.stringify(claims))}.signature`
}
