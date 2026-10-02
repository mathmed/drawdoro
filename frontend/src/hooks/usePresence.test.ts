import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { usePresence } from './usePresence'

describe('usePresence', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should keep the element mounted while it fades out', () => {
    const sut = renderHook(({ visible }) => usePresence(visible, 200), { initialProps: { visible: true } })
    expect(sut.result.current).toEqual({ isMounted: true, isExiting: false })

    sut.rerender({ visible: false })
    expect(sut.result.current).toEqual({ isMounted: true, isExiting: true })

    act(() => vi.advanceTimersByTime(199))
    expect(sut.result.current.isMounted).toBe(true)
    act(() => vi.advanceTimersByTime(1))
    expect(sut.result.current).toEqual({ isMounted: false, isExiting: false })
  })

  it('should mount as soon as it becomes visible and cancel a pending exit', () => {
    const sut = renderHook(({ visible }) => usePresence(visible, 200), { initialProps: { visible: false } })
    expect(sut.result.current.isMounted).toBe(false)

    sut.rerender({ visible: true })
    expect(sut.result.current).toEqual({ isMounted: true, isExiting: false })

    sut.rerender({ visible: false })
    act(() => vi.advanceTimersByTime(100))
    sut.rerender({ visible: true })
    act(() => vi.advanceTimersByTime(500))
    expect(sut.result.current).toEqual({ isMounted: true, isExiting: false })
  })

  it('should clear the exit timer on unmount', () => {
    const sut = renderHook(({ visible }) => usePresence(visible, 200), { initialProps: { visible: true } })
    sut.rerender({ visible: false })
    expect(vi.getTimerCount()).toBe(1)

    sut.unmount()

    expect(vi.getTimerCount()).toBe(0)
  })
})
