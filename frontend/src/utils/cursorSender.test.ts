import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createCursorSender, CURSOR_SEND_INTERVAL_MS } from './cursorSender'

const at = (x: number, y: number, page = 'page:page') => ({ point: { x, y }, page })

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('createCursorSender', () => {
  it('should send the first move right away', () => {
    const send = vi.fn()
    createCursorSender(send).update(at(1, 2))

    expect(send).toHaveBeenCalledExactlyOnceWith(at(1, 2))
  })

  it('should coalesce a burst of moves into one message per interval ending on the latest', () => {
    const send = vi.fn()
    const sender = createCursorSender(send)

    sender.update(at(1, 1))
    sender.update(at(2, 2))
    sender.update(at(3, 3))
    expect(send).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS - 1)
    expect(send).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(1)
    expect(send).toHaveBeenLastCalledWith(at(3, 3))
    expect(send).toHaveBeenCalledTimes(2)
  })

  it('should send at most one message per interval while the pointer keeps moving', () => {
    const send = vi.fn()
    const sender = createCursorSender(send)

    for (let step = 0; step < 1000; step += 4) {
      sender.update(at(step, step))
      vi.advanceTimersByTime(4)
    }

    expect(send.mock.calls.length).toBeLessThanOrEqual(Math.ceil(1000 / CURSOR_SEND_INTERVAL_MS) + 1)
    expect(send.mock.calls.length).toBeGreaterThanOrEqual(Math.floor(1000 / CURSOR_SEND_INTERVAL_MS) - 1)
  })

  it('should skip positions the others already have', () => {
    const send = vi.fn()
    const sender = createCursorSender(send)

    sender.update(at(1.01, 2.04))
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)
    sender.update(at(1.04, 1.96))
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)

    expect(send).toHaveBeenCalledExactlyOnceWith(at(1, 2))
  })

  it('should send a move to another page even at the same spot', () => {
    const send = vi.fn()
    const sender = createCursorSender(send)

    sender.update(at(1, 2))
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)
    sender.update(at(1, 2, 'page:other'))

    expect(send).toHaveBeenLastCalledWith(at(1, 2, 'page:other'))
  })

  it('should say once that the pointer left the canvas', () => {
    const send = vi.fn()
    const sender = createCursorSender(send)

    sender.update(at(1, 2))
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)
    sender.update(null)
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)
    sender.update(null)
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)

    expect(send.mock.calls).toEqual([[at(1, 2)], [null]])
  })

  it('should drop a pending move when disposed', () => {
    const send = vi.fn()
    const sender = createCursorSender(send)
    sender.update(at(1, 2))
    sender.update(at(5, 5))

    sender.dispose()
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS * 2)

    expect(send).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })
})
