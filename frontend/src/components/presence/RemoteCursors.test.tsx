import { act, render } from '@testing-library/react'
import type { Editor } from 'tldraw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { colorFor } from '../../utils/avatar'
import { CURSOR_INACTIVE_MS, RemoteCursorStore, type CursorMessage } from '../../utils/remoteCursors'
import RemoteCursors from './RemoteCursors'

vi.mock('tldraw', () => ({ useValue: (_name: string, compute: () => unknown) => compute() }))

const ANA: CursorMessage = { id: 'user-ana', name: 'Ana', point: { x: 100, y: 50 }, page: 'page:page' }

// The local viewer's camera: what tldraw does to turn page coordinates into screen ones.
const camera = { x: 0, y: 0, z: 1 }

function fakeEditor(pageId = 'page:page'): Editor {
  return {
    getCurrentPageId: () => pageId,
    pageToViewport: (point: { x: number; y: number }) => ({ x: (point.x + camera.x) * camera.z, y: (point.y + camera.y) * camera.z }),
  } as unknown as Editor
}

let frames: Map<number, FrameRequestCallback>
let clock: number
let nextFrame: number

function playFrame(stepMs = 16): void {
  clock += stepMs
  const pending = [...frames.values()]
  frames.clear()
  act(() => pending.forEach((callback) => callback(clock)))
}

function cursorElement(container: HTMLElement, id = ANA.id): HTMLElement | null {
  return container.querySelector(`[data-cursor-id="${id}"]`)
}

function position(element: HTMLElement | null): { x: number; y: number } {
  const match = /translate\((-?[\d.]+)px, (-?[\d.]+)px\)/.exec(element?.style.transform ?? '')
  return { x: Number(match?.[1]), y: Number(match?.[2]) }
}

beforeEach(() => {
  Object.assign(camera, { x: 0, y: 0, z: 1 })
  frames = new Map()
  clock = 0
  nextFrame = 0
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    nextFrame += 1
    frames.set(nextFrame, callback)
    return nextFrame
  })
  vi.stubGlobal('cancelAnimationFrame', (id: number) => frames.delete(id))
  vi.spyOn(performance, 'now').mockImplementation(() => clock)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('RemoteCursors', () => {
  it('should draw each person with their name and presence colour', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())

    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)

    const element = cursorElement(container)
    expect(element).toHaveTextContent('Ana')
    expect(element?.querySelector('.remote-cursor-name')).toHaveStyle({ background: colorFor(ANA.id) })
    expect(element?.querySelector('path')).toHaveAttribute('fill', colorFor(ANA.id))
  })

  it('should place the cursor on this viewer screen from its page coordinates', () => {
    Object.assign(camera, { x: -40, y: 10, z: 2 })
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())

    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)

    expect(position(cursorElement(container))).toEqual({ x: 120, y: 120 })
  })

  it('should follow the local camera when this viewer pans or zooms', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)

    Object.assign(camera, { x: 10, y: 0, z: 0.5 })
    playFrame()

    expect(position(cursorElement(container))).toEqual({ x: 55, y: 25 })
  })

  it('should glide towards a new position instead of jumping to it', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)

    cursors.apply({ ...ANA, point: { x: 200, y: 50 } }, Date.now())
    playFrame()
    const firstFrame = position(cursorElement(container)).x
    expect(firstFrame).toBeGreaterThan(100)
    expect(firstFrame).toBeLessThan(200)

    for (let frame = 0; frame < 60; frame += 1) {
      playFrame()
    }
    expect(position(cursorElement(container))).toEqual({ x: 200, y: 50 })
  })

  it('should only show the cursors on the page this viewer is looking at', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    cursors.apply({ ...ANA, id: 'user-bruno', name: 'Bruno', page: 'page:other' }, Date.now())

    const { container } = render(<RemoteCursors editor={fakeEditor('page:other')} cursors={cursors} />)

    expect(cursorElement(container)).toBeNull()
    expect(cursorElement(container, 'user-bruno')).toHaveTextContent('Bruno')
  })

  it('should remove the cursor when the pointer leaves the canvas and stop animating', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)
    expect(frames.size).toBe(1)

    act(() => cursors.apply({ ...ANA, point: null, page: null }, Date.now()))

    expect(cursorElement(container)).toBeNull()
    expect(frames.size).toBe(0)
  })

  it('should jump straight to where someone comes back instead of gliding from where they left', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)
    act(() => cursors.apply({ ...ANA, point: null, page: null }, Date.now()))

    act(() => cursors.apply({ ...ANA, point: { x: 900, y: 900 } }, Date.now()))

    expect(position(cursorElement(container))).toEqual({ x: 900, y: 900 })
  })

  it('should hide someone who stopped moving for a while', () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    const { container } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)

    act(() => vi.advanceTimersByTime(CURSOR_INACTIVE_MS - 1000))
    expect(cursorElement(container)).not.toBeNull()

    act(() => vi.advanceTimersByTime(1000))
    expect(cursorElement(container)).toBeNull()
  })

  it('should stop its timers and frames when the canvas closes', () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] })
    const cursors = new RemoteCursorStore()
    cursors.apply(ANA, Date.now())
    const { unmount } = render(<RemoteCursors editor={fakeEditor()} cursors={cursors} />)

    unmount()

    expect(vi.getTimerCount()).toBe(0)
    expect(frames.size).toBe(0)
  })
})
