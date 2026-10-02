import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { LOADER_DELAY_MS, LOADER_MIN_VISIBLE_MS, useDelayedVisibility } from './useDelayedVisibility'

function setup(active: boolean, options?: Parameters<typeof useDelayedVisibility>[1]) {
  return renderHook(({ isActive }) => useDelayedVisibility(isActive, options), { initialProps: { isActive: active } })
}

describe('useDelayedVisibility', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should stay hidden until the delay has passed', () => {
    const sut = setup(true)

    expect(sut.result.current).toBe(false)
    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS - 1))
    expect(sut.result.current).toBe(false)
    act(() => vi.advanceTimersByTime(1))
    expect(sut.result.current).toBe(true)
  })

  it('should never show when the work ends before the delay', () => {
    const sut = setup(true)

    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS - 20))
    sut.rerender({ isActive: false })
    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS * 10))

    expect(sut.result.current).toBe(false)
  })

  it('should stay visible for the minimum time once shown', () => {
    const sut = setup(true)
    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS))
    act(() => vi.advanceTimersByTime(100))

    sut.rerender({ isActive: false })
    expect(sut.result.current).toBe(true)
    act(() => vi.advanceTimersByTime(LOADER_MIN_VISIBLE_MS - 101))
    expect(sut.result.current).toBe(true)
    act(() => vi.advanceTimersByTime(1))
    expect(sut.result.current).toBe(false)
  })

  it('should hide at once when it was already visible for the minimum time', () => {
    const sut = setup(true)
    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS + LOADER_MIN_VISIBLE_MS + 50))

    sut.rerender({ isActive: false })
    act(() => vi.advanceTimersByTime(0))

    expect(sut.result.current).toBe(false)
  })

  it('should keep showing when the work restarts during the minimum time', () => {
    const sut = setup(true)
    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS))

    sut.rerender({ isActive: false })
    act(() => vi.advanceTimersByTime(100))
    sut.rerender({ isActive: true })
    act(() => vi.advanceTimersByTime(LOADER_MIN_VISIBLE_MS * 2))

    expect(sut.result.current).toBe(true)
  })

  it('should show straight away without a delay', () => {
    const sut = setup(true, { delayMs: 0 })

    expect(sut.result.current).toBe(true)
  })

  it('should honour custom delay and minimum times', () => {
    const sut = setup(true, { delayMs: 50, minVisibleMs: 1000 })
    act(() => vi.advanceTimersByTime(50))
    expect(sut.result.current).toBe(true)

    sut.rerender({ isActive: false })
    act(() => vi.advanceTimersByTime(999))
    expect(sut.result.current).toBe(true)
    act(() => vi.advanceTimersByTime(1))
    expect(sut.result.current).toBe(false)
  })

  it('should clear its timers on unmount', () => {
    const sut = setup(true)
    expect(vi.getTimerCount()).toBe(1)

    sut.unmount()

    expect(vi.getTimerCount()).toBe(0)
  })
})
