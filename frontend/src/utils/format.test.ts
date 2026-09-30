import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { initial, slugify, timeAgo } from './format'

describe('slugify', () => {
  it.each([
    ['Acme', 'acme'],
    ['Acme Draw', 'acme-draw'],
    ['  São Paulo — Núcleo  ', 'sao-paulo-nucleo'],
    ['API/Gateway v2', 'api-gateway-v2'],
    ['---', ''],
  ])('should turn %j into %j', (value, expected) => {
    expect(slugify(value)).toBe(expected)
  })
})

describe('initial', () => {
  it.each([
    ['ana', 'A'],
    ['  bruno', 'B'],
    ['', '?'],
    ['   ', '?'],
    [undefined, '?'],
  ])('should turn %j into %j', (value, expected) => {
    expect(initial(value)).toBe(expected)
  })
})

describe('timeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-10T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should return an empty string when there is no timestamp', () => {
    expect(timeAgo(undefined)).toBe('')
  })

  it('should read naive API timestamps as UTC', () => {
    expect(timeAgo('2026-03-10T11:00:00')).toBe('1 hour ago')
  })

  it('should honour an explicit offset', () => {
    expect(timeAgo('2026-03-10T08:00:00-03:00')).toBe('1 hour ago')
    expect(timeAgo('2026-03-10T09:00:00Z')).toBe('3 hours ago')
  })

  it('should say "just now" under a minute', () => {
    expect(timeAgo('2026-03-10T11:59:30Z')).toBe('just now')
  })

  it('should pick the largest fitting unit', () => {
    expect(timeAgo('2026-03-09T12:00:00Z')).toBe('yesterday')
    expect(timeAgo('2026-02-24T12:00:00Z')).toBe('2 weeks ago')
    expect(timeAgo('2025-03-10T12:00:00Z')).toBe('last year')
  })
})
