import { describe, expect, it, vi } from 'vitest'

import { colorFor } from './avatar'
import {
  approach,
  CURSOR_INACTIVE_MS,
  CURSOR_SMOOTHING_MS,
  parseCursorMessage,
  RemoteCursorStore,
  type CursorMessage,
} from './remoteCursors'

const ANA: CursorMessage = { id: 'user-ana', name: 'Ana', point: { x: 10, y: 20 }, page: 'page:page' }

describe('parseCursorMessage', () => {
  it('should read a cursor on the canvas', () => {
    expect(parseCursorMessage({ type: 'cursor', ...ANA })).toEqual(ANA)
  })

  it('should read a pointer that left the canvas', () => {
    expect(parseCursorMessage({ type: 'cursor', id: 'a', name: 'Ana', point: null, page: null })).toEqual({
      id: 'a',
      name: 'Ana',
      point: null,
      page: null,
    })
  })

  it.each([
    null,
    'cursor',
    [ANA],
    { ...ANA, id: 1 },
    { ...ANA, name: undefined },
    { ...ANA, point: undefined },
    { ...ANA, point: [1, 2] },
    { ...ANA, point: { x: 1 } },
    { ...ANA, point: { x: '1', y: 2 } },
    { ...ANA, point: { x: Number.NaN, y: 2 } },
    { ...ANA, point: { x: 1, y: Number.POSITIVE_INFINITY } },
    { ...ANA, page: null },
  ])('should ignore a malformed cursor %#', (message) => {
    expect(parseCursorMessage(message)).toBeNull()
  })
})

describe('approach', () => {
  it('should ease part of the way in one frame and almost all of it after a while', () => {
    const halfway = approach({ x: 0, y: 0 }, { x: 100, y: -100 }, CURSOR_SMOOTHING_MS * Math.LN2)
    expect(halfway.x).toBeCloseTo(50)
    expect(halfway.y).toBeCloseTo(-50)

    const later = approach({ x: 0, y: 0 }, { x: 100, y: 0 }, CURSOR_SMOOTHING_MS * 10)
    expect(later.x).toBeGreaterThan(99.99)
  })

  it('should stay put when no time passed', () => {
    expect(approach({ x: 0, y: 0 }, { x: 100, y: 0 }, 0)).toEqual({ x: 0, y: 0 })
  })

  it('should land on the target once it is close enough', () => {
    expect(approach({ x: 9.99, y: 5 }, { x: 10, y: 5 }, 1)).toEqual({ x: 10, y: 5 })
  })
})

describe('RemoteCursorStore', () => {
  function storeWithListener() {
    const store = new RemoteCursorStore()
    const listener = vi.fn()
    store.subscribe(listener)
    return { store, listener }
  }

  it('should add a cursor with the colour of the person in the presence', () => {
    const { store, listener } = storeWithListener()

    store.apply(ANA, 1000)

    expect(store.list()).toEqual([
      { id: 'user-ana', name: 'Ana', color: colorFor('user-ana'), pageId: 'page:page', target: { x: 10, y: 20 }, lastSeenAt: 1000 },
    ])
    expect(listener).toHaveBeenCalledTimes(1)
  })

  it('should move a cursor without telling the subscribers', () => {
    const { store, listener } = storeWithListener()
    store.apply(ANA, 1000)
    const before = store.list()

    store.apply({ ...ANA, point: { x: 30, y: 40 } }, 2000)

    expect(listener).toHaveBeenCalledTimes(1)
    expect(store.list()).toBe(before)
    expect(store.list()[0]).toMatchObject({ target: { x: 30, y: 40 }, lastSeenAt: 2000 })
  })

  it('should tell the subscribers when a cursor changes page or name', () => {
    const { store, listener } = storeWithListener()
    store.apply(ANA, 1000)

    store.apply({ ...ANA, page: 'page:other' }, 1100)
    store.apply({ ...ANA, page: 'page:other', name: 'Ana Maria' }, 1200)

    expect(listener).toHaveBeenCalledTimes(3)
    expect(store.list()).toHaveLength(1)
    expect(store.list()[0]).toMatchObject({ name: 'Ana Maria', pageId: 'page:other' })
  })

  it('should remove a cursor whose pointer left the canvas', () => {
    const { store, listener } = storeWithListener()
    store.apply(ANA, 1000)

    store.apply({ ...ANA, point: null, page: null }, 1100)
    store.apply({ ...ANA, point: null, page: null }, 1200)

    expect(store.list()).toEqual([])
    expect(listener).toHaveBeenCalledTimes(2)
  })

  it('should drop the cursors of people who left the diagram', () => {
    const { store } = storeWithListener()
    store.apply(ANA, 1000)
    store.apply({ ...ANA, id: 'user-bruno', name: 'Bruno' }, 1000)

    store.retain(new Set(['user-bruno', 'agent:claude']))

    expect(store.list().map((cursor) => cursor.id)).toEqual(['user-bruno'])
  })

  it('should hide cursors that went quiet for too long', () => {
    const { store, listener } = storeWithListener()
    store.apply(ANA, 1000)
    store.apply({ ...ANA, id: 'user-bruno', name: 'Bruno' }, 5000)

    store.sweep(1000 + CURSOR_INACTIVE_MS - 1)
    expect(store.list()).toHaveLength(2)

    store.sweep(1000 + CURSOR_INACTIVE_MS)
    expect(store.list().map((cursor) => cursor.id)).toEqual(['user-bruno'])
    expect(listener).toHaveBeenCalledTimes(3)
  })

  it('should clear every cursor and stop telling unsubscribed listeners', () => {
    const store = new RemoteCursorStore()
    const listener = vi.fn()
    const unsubscribe = store.subscribe(listener)
    store.apply(ANA, 1000)
    unsubscribe()

    store.clear()
    store.clear()

    expect(store.list()).toEqual([])
    expect(listener).toHaveBeenCalledTimes(1)
  })
})
