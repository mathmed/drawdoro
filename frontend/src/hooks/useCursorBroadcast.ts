import { useEffect } from 'react'
import { react, type Editor } from 'tldraw'

import { createCursorSender } from '../utils/cursorSender'
import type { CursorPosition } from '../utils/remoteCursors'

interface ScreenPoint {
  x: number
  y: number
}

// Shares where the local pointer is on the canvas, in page coordinates, while it is over the canvas.
export function useCursorBroadcast(editor: Editor | null, sendCursor: (position: CursorPosition | null) => void): void {
  useEffect(() => {
    if (editor === null) {
      return undefined
    }
    const canvas = editor
    const container = editor.getContainer()
    const sender = createCursorSender(sendCursor)
    let pointer: ScreenPoint | null = null

    function share(): void {
      if (pointer === null) {
        sender.update(null)
        return
      }
      const point = canvas.screenToPage(pointer)
      sender.update({ point: { x: point.x, y: point.y }, page: canvas.getCurrentPageId() })
    }

    function handleMove(event: PointerEvent): void {
      pointer = { x: event.clientX, y: event.clientY }
      share()
    }

    function handleLeave(): void {
      pointer = null
      share()
    }

    container.addEventListener('pointermove', handleMove)
    container.addEventListener('pointerleave', handleLeave)
    // Panning or zooming under a still pointer (wheel, presentation slides) moves it on the canvas too.
    const stopFollowingCamera = react('share cursor when the camera moves', () => {
      editor.getCamera()
      editor.getCurrentPageId()
      if (pointer !== null) {
        share()
      }
    })

    return () => {
      container.removeEventListener('pointermove', handleMove)
      container.removeEventListener('pointerleave', handleLeave)
      stopFollowingCamera()
      sender.dispose()
    }
  }, [editor, sendCursor])
}
