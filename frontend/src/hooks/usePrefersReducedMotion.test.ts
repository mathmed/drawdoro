import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { stubReducedMotion } from '../test/reducedMotion'
import { usePrefersReducedMotion } from './usePrefersReducedMotion'

describe('usePrefersReducedMotion', () => {
  it('should be false where matchMedia is not available', () => {
    const sut = renderHook(() => usePrefersReducedMotion())

    expect(sut.result.current).toBe(false)
  })

  it('should follow the operating system setting', () => {
    const media = stubReducedMotion(true)
    const sut = renderHook(() => usePrefersReducedMotion())
    expect(sut.result.current).toBe(true)

    act(() => media.setReduced(false))

    expect(sut.result.current).toBe(false)
  })
})
