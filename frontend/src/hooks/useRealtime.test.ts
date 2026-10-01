import { renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

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
})
