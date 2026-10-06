import { renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { RemoteCursorStore } from '../utils/remoteCursors'
import { useRealtime } from './useRealtime'

vi.mock('tldraw', () => ({ loadSnapshot: vi.fn() }))
vi.mock('../auth/config', () => ({ authConfig: { enabled: false } }))
vi.mock('../auth/session', () => ({ getIdToken: vi.fn() }))

class FakeSocket {
  static last: FakeSocket | null = null
  static readonly OPEN = 1
  readyState = 1
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null

  constructor(readonly url: string) {
    FakeSocket.last = this
  }

  send = vi.fn()
  close = vi.fn()

  receive(message: object): void {
    this.onmessage?.({ data: JSON.stringify(message) })
  }

  receiveRaw(data: string): void {
    this.onmessage?.({ data })
  }
}

beforeEach(() => {
  FakeSocket.last = null
  vi.stubGlobal('WebSocket', FakeSocket)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useRealtime', () => {
  it('should reload comments when someone changes them', async () => {
    const onCommentsChanged = vi.fn()
    const onPresenceChange = vi.fn()
    renderHook(() => useRealtime({ diagramId: 'd1', editor: null, onPresenceChange, onCommentsChanged }))
    await vi.waitFor(() => expect(FakeSocket.last).not.toBeNull())

    FakeSocket.last?.receive({ type: 'comments_changed', diagram_id: 'd1' })

    expect(onCommentsChanged).toHaveBeenCalledTimes(1)
    expect(onPresenceChange).not.toHaveBeenCalled()
  })

  describe('cursors', () => {
    const presence = { type: 'presence', users: [{ id: 'me', name: 'Me' }, { id: 'ana', name: 'Ana' }], you: 'me' }
    const anaCursor = { type: 'cursor', id: 'ana', name: 'Ana', point: { x: 5, y: 6 }, page: 'page:page' }

    async function connected(remoteCursors: RemoteCursorStore) {
      const hook = renderHook(() => useRealtime({ diagramId: 'd1', editor: null, onPresenceChange: vi.fn(), remoteCursors }))
      await vi.waitFor(() => expect(FakeSocket.last).not.toBeNull())
      FakeSocket.last?.receive(presence)
      return { hook, socket: FakeSocket.last! }
    }

    it('should show the cursor of someone else in the diagram', async () => {
      const store = new RemoteCursorStore()
      const { socket } = await connected(store)

      socket.receive(anaCursor)

      expect(store.list()).toMatchObject([{ id: 'ana', name: 'Ana', target: { x: 5, y: 6 }, pageId: 'page:page' }])
    })

    it('should never show this person their own cursor from another tab', async () => {
      const store = new RemoteCursorStore()
      const { socket } = await connected(store)

      socket.receive({ ...anaCursor, id: 'me', name: 'Me' })

      expect(store.list()).toEqual([])
    })

    it('should survive cursors it does not understand and frames that are not json', async () => {
      const store = new RemoteCursorStore()
      const onCommentsChanged = vi.fn()
      renderHook(() => useRealtime({ diagramId: 'd1', editor: null, onPresenceChange: vi.fn(), onCommentsChanged, remoteCursors: store }))
      await vi.waitFor(() => expect(FakeSocket.last).not.toBeNull())
      const socket = FakeSocket.last!

      socket.receive({ type: 'cursor', id: 'ana', x: 1 })
      socket.receiveRaw('not json')
      socket.receive({ type: 'cursor_v2', id: 'ana' })
      socket.receive({ type: 'comments_changed' })

      expect(store.list()).toEqual([])
      expect(onCommentsChanged).toHaveBeenCalledTimes(1)
    })

    it('should remove the cursor of someone who left the diagram', async () => {
      const store = new RemoteCursorStore()
      const { socket } = await connected(store)
      socket.receive(anaCursor)

      socket.receive({ ...presence, users: [{ id: 'me', name: 'Me' }] })

      expect(store.list()).toEqual([])
    })

    it('should clear the cursors when the connection drops or the canvas closes', async () => {
      const store = new RemoteCursorStore()
      const { hook, socket } = await connected(store)
      socket.receive(anaCursor)
      socket.onclose?.()
      expect(store.list()).toEqual([])

      store.apply({ id: 'bruno', name: 'Bruno', point: { x: 0, y: 0 }, page: 'page:page' }, 0)
      hook.unmount()
      expect(store.list()).toEqual([])
    })

    it('should send its own pointer in page coordinates and when it leaves the canvas', async () => {
      const { hook, socket } = await connected(new RemoteCursorStore())

      hook.result.current.sendCursor({ point: { x: 1.5, y: -2 }, page: 'page:page' })
      hook.result.current.sendCursor(null)

      expect(socket.send.mock.calls.map(([data]) => JSON.parse(data as string))).toEqual([
        { type: 'cursor', point: { x: 1.5, y: -2 }, page: 'page:page' },
        { type: 'cursor', point: null },
      ])
    })

    it('should not send its pointer while the socket is not open', async () => {
      const { hook, socket } = await connected(new RemoteCursorStore())
      socket.readyState = 0

      hook.result.current.sendCursor({ point: { x: 1, y: 2 }, page: 'page:page' })

      expect(socket.send).not.toHaveBeenCalled()
    })
  })
})
