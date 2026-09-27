import { Tldraw, type Editor, type TLStoreSnapshot } from 'tldraw'
import 'tldraw/tldraw.css'

import type { CanvasState, Diagram } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'

interface DrawingCanvasProps {
  diagram: Diagram
}

export default function DrawingCanvas({ diagram }: DrawingCanvasProps) {
  const saveCanvasState = useAppStore((state) => state.saveCanvasState)

  function handleMount(editor: Editor): void {
    if (diagram.canvas_state !== null) {
      editor.store.loadSnapshot(diagram.canvas_state as unknown as TLStoreSnapshot)
    }

    let timer: ReturnType<typeof setTimeout>
    editor.store.listen(
      () => {
        clearTimeout(timer)
        timer = setTimeout(() => {
          const snapshot = editor.store.getSnapshot()
          void saveCanvasState(snapshot as unknown as CanvasState)
        }, 1500)
      },
      { scope: 'document' },
    )
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Tldraw onMount={handleMount} inferDarkMode />
    </div>
  )
}
