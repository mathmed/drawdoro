import { act, renderHook } from '@testing-library/react'
import type { Editor } from 'tldraw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Diagram } from '../api/types'
import { useAppStore } from '../store/useAppStore'
import { useThumbnailStore } from '../store/useThumbnailStore'
import { THUMBNAIL_REFRESH_DELAY_MS, useDiagramThumbnail } from './useDiagramThumbnail'

const authConfig = vi.hoisted(() => ({ enabled: true }))

vi.mock('../auth/config', () => ({ authConfig }))

const DIAGRAM: Diagram = {
  id: 'd1',
  project_id: 'p1',
  folder_id: null,
  name: 'Checkout',
  canvas_state: null,
  updated_at: '2026-10-06T12:00:00',
}
const TARGET = { projectId: 'p1', diagramId: 'd1', version: '2026-10-06T12:00:00' }

let readonly = false
const listeners = new Set<() => void>()
const listen = vi.fn((listener: () => void) => {
  listeners.add(listener)
  return () => listeners.delete(listener)
})
const editor = { getIsReadonly: () => readonly, store: { listen } } as unknown as Editor

function edit(): void {
  act(() => listeners.forEach((listener) => listener()))
}
const capture = vi.fn(async () => undefined)
const needsRefresh = vi.fn()

beforeEach(() => {
  vi.useFakeTimers()
  readonly = false
  authConfig.enabled = true
  capture.mockClear()
  listen.mockClear()
  listeners.clear()
  needsRefresh.mockReset().mockReturnValue(true)
  useAppStore.setState({ ...useAppStore.getInitialState(), activeDiagram: DIAGRAM, myRole: 'editor' }, true)
  useThumbnailStore.setState({ capture, needsRefresh })
})

afterEach(() => {
  vi.useRealTimers()
})

function later(ms = THUMBNAIL_REFRESH_DELAY_MS): void {
  act(() => {
    vi.advanceTimersByTime(ms)
  })
}

describe('useDiagramThumbnail', () => {
  it('should capture the preview a moment after the diagram opens', () => {
    renderHook(() => useDiagramThumbnail(editor))

    later(THUMBNAIL_REFRESH_DELAY_MS - 1)
    expect(capture).not.toHaveBeenCalled()
    later(1)

    expect(needsRefresh).toHaveBeenCalledWith(TARGET)
    expect(capture).toHaveBeenCalledExactlyOnceWith(editor, TARGET)
  })

  it('should capture once after a burst of saved versions, for the last one', () => {
    renderHook(() => useDiagramThumbnail(editor))

    later(1000)
    act(() => useAppStore.setState({ activeDiagram: { ...DIAGRAM, updated_at: '2026-10-06T12:00:01' } }))
    later(1000)
    act(() => useAppStore.setState({ activeDiagram: { ...DIAGRAM, updated_at: '2026-10-06T12:00:02' } }))
    later()

    expect(capture).toHaveBeenCalledExactlyOnceWith(editor, { ...TARGET, version: '2026-10-06T12:00:02' })
  })

  it('should wait until the local edits pause, so it never renders mid-gesture', () => {
    renderHook(() => useDiagramThumbnail(editor))

    later(1500)
    edit()
    later(1500)
    edit()
    later(THUMBNAIL_REFRESH_DELAY_MS - 1)
    expect(capture).not.toHaveBeenCalled()
    later(1)

    expect(capture).toHaveBeenCalledOnce()
    expect(listen).toHaveBeenCalledWith(expect.any(Function), { scope: 'document', source: 'user' })
  })

  it('should stop listening to edits when the diagram closes', () => {
    const { unmount } = renderHook(() => useDiagramThumbnail(editor))

    unmount()

    expect(listeners.size).toBe(0)
  })

  it('should not capture when the stored preview is already up to date', () => {
    needsRefresh.mockReturnValue(false)
    renderHook(() => useDiagramThumbnail(editor))

    later()

    expect(capture).not.toHaveBeenCalled()
  })

  it.each(['viewer', null] as const)('should never capture for a %s', (role) => {
    useAppStore.setState({ myRole: role })
    renderHook(() => useDiagramThumbnail(editor))

    later()

    expect(capture).not.toHaveBeenCalled()
  })

  it('should capture for anyone when sign-in is off', () => {
    authConfig.enabled = false
    useAppStore.setState({ myRole: null })
    renderHook(() => useDiagramThumbnail(editor))

    later()

    expect(capture).toHaveBeenCalledOnce()
  })

  it('should not capture from a read-only canvas', () => {
    readonly = true
    renderHook(() => useDiagramThumbnail(editor))

    later()

    expect(capture).not.toHaveBeenCalled()
  })

  it('should wait for the editor and a diagram', () => {
    useAppStore.setState({ activeDiagram: null })
    const { rerender } = renderHook(({ current }) => useDiagramThumbnail(current), {
      initialProps: { current: null as Editor | null },
    })

    later()
    rerender({ current: editor })
    later()

    expect(capture).not.toHaveBeenCalled()
  })

  it('should drop a pending capture when the diagram closes', () => {
    const { unmount } = renderHook(() => useDiagramThumbnail(editor))

    later(1000)
    unmount()
    later()

    expect(capture).not.toHaveBeenCalled()
  })
})
