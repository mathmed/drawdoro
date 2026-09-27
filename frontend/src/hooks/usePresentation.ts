import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Editor, TLShapeId } from 'tldraw'

interface UsePresentationResult {
  frameCount: number
  currentIndex: number
  goToNext: () => void
  goToPrevious: () => void
}

// Drives the presentation navigation: it collects the frame shapes of the current
// page and zooms the camera to each one as the user steps through them.
export function usePresentation(editor: Editor | null, active: boolean): UsePresentationResult {
  const [currentIndex, setCurrentIndex] = useState(0)

  const frameIds = useMemo<TLShapeId[]>(() => {
    if (editor === null || !active) {
      return []
    }
    return editor
      .getCurrentPageShapes()
      .filter((shape) => shape.type === 'frame')
      .map((shape) => shape.id)
  }, [editor, active])

  const zoomTo = useCallback(
    (index: number) => {
      if (editor === null || frameIds.length === 0) {
        return
      }
      const frameId = frameIds[index]
      const bounds = editor.getShapePageBounds(frameId)
      if (bounds !== undefined) {
        editor.zoomToBounds(bounds, { animation: { duration: 320 }, inset: 0 })
      }
    },
    [editor, frameIds],
  )

  useEffect(() => {
    if (!active) {
      return
    }
    setCurrentIndex(0)
    zoomTo(0)
  }, [active, zoomTo])

  const goToNext = useCallback(() => {
    setCurrentIndex((index) => {
      const next = Math.min(index + 1, frameIds.length - 1)
      zoomTo(next)
      return next
    })
  }, [frameIds.length, zoomTo])

  const goToPrevious = useCallback(() => {
    setCurrentIndex((index) => {
      const previous = Math.max(index - 1, 0)
      zoomTo(previous)
      return previous
    })
  }, [zoomTo])

  return { frameCount: frameIds.length, currentIndex, goToNext, goToPrevious }
}
