import { renderHook } from '@testing-library/react'
import type { Editor } from 'tldraw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CURSOR_SEND_INTERVAL_MS } from '../utils/cursorSender'
import { useCursorBroadcast } from './useCursorBroadcast'

const reactions = vi.hoisted(() => ({ active: new Set<() => void>() }))

vi.mock('tldraw', () => ({
  react: (_name: string, effect: () => void) => {
    reactions.active.add(effect)
    effect()
    return () => reactions.active.delete(effect)
  },
}))

// The local camera: the canvas is panned by (x, y) and zoomed by z.
const camera = { x: 0, y: 0, z: 1 }

function fakeEditor(container: HTMLElement): Editor {
  return {
    getContainer: () => container,
    getCamera: () => camera,
    getCurrentPageId: () => 'page:page',
    screenToPage: (point: { x: number; y: number }) => ({ x: point.x / camera.z - camera.x, y: point.y / camera.z - camera.y, z: 0.5 }),
  } as unknown as Editor
}

function moveCamera(next: Partial<typeof camera>): void {
  Object.assign(camera, next)
  reactions.active.forEach((effect) => effect())
}

function pointerMove(target: HTMLElement, x: number, y: number): void {
  const event = new MouseEvent('pointermove', { clientX: x, clientY: y })
  target.dispatchEvent(event)
}

let container: HTMLElement

beforeEach(() => {
  vi.useFakeTimers()
  Object.assign(camera, { x: 0, y: 0, z: 1 })
  reactions.active.clear()
  container = document.createElement('div')
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useCursorBroadcast', () => {
  it('should send where the pointer is on the canvas in page coordinates', () => {
    Object.assign(camera, { x: 10, y: -5, z: 2 })
    const sendCursor = vi.fn()
    renderHook(() => useCursorBroadcast(fakeEditor(container), sendCursor))

    pointerMove(container, 100, 40)

    expect(sendCursor).toHaveBeenCalledExactlyOnceWith({ point: { x: 40, y: 25 }, page: 'page:page' })
  })

  it('should throttle a fast moving pointer', () => {
    const sendCursor = vi.fn()
    renderHook(() => useCursorBroadcast(fakeEditor(container), sendCursor))

    for (let step = 0; step < 10; step += 1) {
      pointerMove(container, step, step)
    }
    expect(sendCursor).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)
    expect(sendCursor).toHaveBeenCalledTimes(2)
    expect(sendCursor).toHaveBeenLastCalledWith({ point: { x: 9, y: 9 }, page: 'page:page' })
  })

  it('should say when the pointer leaves the canvas', () => {
    const sendCursor = vi.fn()
    renderHook(() => useCursorBroadcast(fakeEditor(container), sendCursor))
    pointerMove(container, 1, 1)
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)

    container.dispatchEvent(new MouseEvent('pointerleave'))

    expect(sendCursor).toHaveBeenLastCalledWith(null)
  })

  it('should send the new spot under a still pointer when the camera moves', () => {
    const sendCursor = vi.fn()
    renderHook(() => useCursorBroadcast(fakeEditor(container), sendCursor))
    pointerMove(container, 50, 50)
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)

    moveCamera({ x: -100, z: 0.5 })

    expect(sendCursor).toHaveBeenLastCalledWith({ point: { x: 200, y: 100 }, page: 'page:page' })
  })

  it('should not send anything when the camera moves without the pointer on the canvas', () => {
    const sendCursor = vi.fn()
    renderHook(() => useCursorBroadcast(fakeEditor(container), sendCursor))

    moveCamera({ x: 30 })

    expect(sendCursor).not.toHaveBeenCalled()
  })

  it('should stop listening and drop pending moves when the canvas closes', () => {
    const sendCursor = vi.fn()
    const { unmount } = renderHook(() => useCursorBroadcast(fakeEditor(container), sendCursor))
    pointerMove(container, 1, 1)
    pointerMove(container, 2, 2)

    unmount()
    vi.advanceTimersByTime(CURSOR_SEND_INTERVAL_MS)
    pointerMove(container, 3, 3)
    moveCamera({ x: 5 })

    expect(sendCursor).toHaveBeenCalledTimes(1)
    expect(reactions.active.size).toBe(0)
  })

  it('should do nothing until the editor is ready', () => {
    const sendCursor = vi.fn()
    renderHook(() => useCursorBroadcast(null, sendCursor))

    expect(reactions.active.size).toBe(0)
    expect(sendCursor).not.toHaveBeenCalled()
  })
})
