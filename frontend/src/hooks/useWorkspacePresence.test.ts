import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useWorkspacePresenceStore } from '../store/useWorkspacePresenceStore'
import { useWorkspacePresence } from './useWorkspacePresence'

const auth = vi.hoisted(() => ({ enabled: true }))
vi.mock('../auth/config', () => ({ authConfig: auth }))
vi.mock('../auth/session', () => ({ getIdToken: vi.fn(async () => 'id-token') }))

class FakeSocket {
  static all: FakeSocket[] = []
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: ((event: { code: number }) => void) | null = null

  constructor(readonly url: string) {
    FakeSocket.all.push(this)
  }

  close = vi.fn()

  receive(message: object | string): void {
    act(() => this.onmessage?.({ data: typeof message === 'string' ? message : JSON.stringify(message) }))
  }

  drop(code = 1006): void {
    act(() => this.onclose?.({ code }))
  }
}

function lastSocket(): FakeSocket {
  return FakeSocket.all[FakeSocket.all.length - 1]
}

const ANA = { id: 'u-ana', name: 'Ana', kind: 'person', picture_url: 'https://example.com/ana.png' }
const SNAPSHOT = {
  type: 'presence_snapshot',
  you: 'u-bruno',
  diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [ANA] }],
}

async function opened(workspaceId: string | null = 'w1') {
  const hook = renderHook(({ id }) => useWorkspacePresence(id), { initialProps: { id: workspaceId } })
  await vi.waitFor(() => expect(FakeSocket.all).toHaveLength(1))
  return hook
}

beforeEach(() => {
  auth.enabled = true
  FakeSocket.all = []
  vi.stubGlobal('WebSocket', FakeSocket)
  useWorkspacePresenceStore.getState().reset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useWorkspacePresence', () => {
  it('should subscribe to the workspace with the session token', async () => {
    await opened()

    expect(lastSocket().url).toBe(`ws://${window.location.host}/api/ws/workspaces/w1/presence?token=id-token`)
  })

  it('should subscribe without a token when login is disabled', async () => {
    auth.enabled = false
    await opened()

    expect(lastSocket().url).toBe(`ws://${window.location.host}/api/ws/workspaces/w1/presence`)
  })

  it('should not subscribe before a workspace is chosen', async () => {
    renderHook(() => useWorkspacePresence(null))
    await Promise.resolve()

    expect(FakeSocket.all).toEqual([])
  })

  it('should keep the sidebar presence up to date in real time', async () => {
    await opened()

    lastSocket().receive(SNAPSHOT)
    expect(useWorkspacePresenceStore.getState().you).toBe('u-bruno')
    expect(useWorkspacePresenceStore.getState().byProject.p1).toEqual([ANA])

    lastSocket().receive({ type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [] }] })
    expect(useWorkspacePresenceStore.getState().byDiagram).toEqual({})
    expect(useWorkspacePresenceStore.getState().byProject).toEqual({})
  })

  it('should ignore frames it does not understand', async () => {
    await opened()
    lastSocket().receive(SNAPSHOT)

    lastSocket().receive('not json')
    lastSocket().receive({ type: 'presence_delta', diagrams: [{ diagram_id: 'd1' }] })
    lastSocket().receive({ type: 'cursor', id: 'u-ana' })

    expect(useWorkspacePresenceStore.getState().byProject.p1).toEqual([ANA])
  })

  it('should forget the presence and reconnect shortly when the connection drops', async () => {
    await opened()
    vi.useFakeTimers()
    lastSocket().receive(SNAPSHOT)

    lastSocket().drop()
    expect(useWorkspacePresenceStore.getState().byProject).toEqual({})

    await act(() => vi.advanceTimersByTimeAsync(1999))
    expect(FakeSocket.all).toHaveLength(1)
    await act(() => vi.advanceTimersByTimeAsync(1))
    expect(FakeSocket.all).toHaveLength(2)
  })

  it('should wait much longer before asking again after being refused', async () => {
    await opened()
    vi.useFakeTimers()

    lastSocket().drop(1008)

    await act(() => vi.advanceTimersByTimeAsync(29_999))
    expect(FakeSocket.all).toHaveLength(1)
    await act(() => vi.advanceTimersByTimeAsync(1))
    expect(FakeSocket.all).toHaveLength(2)
  })

  it('should close and forget everything when the sidebar goes away', async () => {
    const hook = await opened()
    vi.useFakeTimers()
    const socket = lastSocket()
    socket.receive(SNAPSHOT)

    hook.unmount()
    socket.drop()
    await act(() => vi.advanceTimersByTimeAsync(60_000))

    expect(socket.close).toHaveBeenCalledTimes(1)
    expect(FakeSocket.all).toHaveLength(1)
    expect(useWorkspacePresenceStore.getState()).toMatchObject({ you: null, byDiagram: {}, byProject: {} })
  })

  it('should switch subscriptions with the workspace', async () => {
    const hook = await opened()
    const first = lastSocket()
    first.receive(SNAPSHOT)

    hook.rerender({ id: 'w2' })
    await vi.waitFor(() => expect(FakeSocket.all).toHaveLength(2))

    expect(first.close).toHaveBeenCalledTimes(1)
    expect(lastSocket().url).toContain('/api/ws/workspaces/w2/presence')
    expect(useWorkspacePresenceStore.getState().byProject).toEqual({})
  })

  it('should not open a socket when it is gone before the token arrives', async () => {
    const hook = renderHook(() => useWorkspacePresence('w1'))
    hook.unmount()
    await Promise.resolve()
    await Promise.resolve()

    expect(FakeSocket.all).toEqual([])
  })
})
