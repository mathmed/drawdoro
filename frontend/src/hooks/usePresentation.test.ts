import { act, renderHook } from '@testing-library/react'
import type { Editor } from 'tldraw'
import { describe, expect, it, vi } from 'vitest'

import { usePresentation } from './usePresentation'

function fakeEditor(): Editor {
  const shapes = [
    { id: 'shape:a', type: 'frame' },
    { id: 'shape:note', type: 'note' },
    { id: 'shape:b', type: 'frame' },
  ]
  return {
    getCurrentPageShapes: () => shapes,
    getShapePageBounds: (id: string) => ({ id }),
    zoomToBounds: vi.fn(),
  } as unknown as Editor
}

describe('usePresentation', () => {
  it('should step through the frames and start again from the first one when restarted', () => {
    const editor = fakeEditor()
    const sut = renderHook(({ active }) => usePresentation(editor, active), { initialProps: { active: true } })
    expect(sut.result.current.frameCount).toBe(2)
    expect(editor.zoomToBounds).toHaveBeenLastCalledWith({ id: 'shape:a' }, expect.anything())

    act(() => sut.result.current.goToNext())
    act(() => sut.result.current.goToNext())
    expect(sut.result.current.currentIndex).toBe(1)
    expect(editor.zoomToBounds).toHaveBeenLastCalledWith({ id: 'shape:b' }, expect.anything())

    sut.rerender({ active: false })
    sut.rerender({ active: true })
    expect(sut.result.current.currentIndex).toBe(0)
    expect(editor.zoomToBounds).toHaveBeenLastCalledWith({ id: 'shape:a' }, expect.anything())

    act(() => sut.result.current.goToPrevious())
    expect(sut.result.current.currentIndex).toBe(0)
  })

  it('should not move the camera while it is not presenting', () => {
    const editor = fakeEditor()
    const sut = renderHook(() => usePresentation(editor, false))

    act(() => sut.result.current.goToNext())

    expect(sut.result.current.frameCount).toBe(0)
    expect(editor.zoomToBounds).not.toHaveBeenCalled()
  })
})
