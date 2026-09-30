import { describe, expect, it } from 'vitest'

import { isOlder } from './freshness'

describe('isOlder', () => {
  it('should detect an older timestamp', () => {
    expect(isOlder('2026-01-01T10:00:00Z', '2026-01-01T10:00:01Z')).toBe(true)
  })

  it('should not treat equal or newer timestamps as older', () => {
    expect(isOlder('2026-01-01T10:00:00Z', '2026-01-01T10:00:00Z')).toBe(false)
    expect(isOlder('2026-01-01T11:00:00Z', '2026-01-01T10:00:00Z')).toBe(false)
  })

  it('should never treat a missing timestamp as older', () => {
    expect(isOlder(undefined, '2026-01-01T10:00:00Z')).toBe(false)
    expect(isOlder('2026-01-01T10:00:00Z', undefined)).toBe(false)
  })
})
