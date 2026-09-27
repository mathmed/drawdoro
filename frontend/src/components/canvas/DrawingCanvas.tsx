import {
  DefaultContextMenu,
  DefaultContextMenuContent,
  Tldraw,
  TldrawUiMenuGroup,
  TldrawUiMenuItem,
  useEditor,
  type Editor,
  type TLComponents,
  type TLStoreSnapshot,
  type TLUiContextMenuProps,
} from 'tldraw'
import 'tldraw/tldraw.css'

import type { CanvasState, Diagram } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import CommentBadge from '../comments/CommentBadge'

interface DrawingCanvasProps {
  diagram: Diagram
}

function CustomContextMenu(props: TLUiContextMenuProps) {
  const editor = useEditor()
  const setActiveElement = useAppStore((state) => state.setActiveElement)
  const isCommentsPanelOpen = useAppStore((state) => state.isCommentsPanelOpen)
  const toggleCommentsPanel = useAppStore((state) => state.toggleCommentsPanel)
  const selectedId = editor.getOnlySelectedShapeId()

  function handleComment(): void {
    if (selectedId === null) {
      return
    }
    setActiveElement(selectedId)
    if (!isCommentsPanelOpen) {
      toggleCommentsPanel()
    }
  }

  return (
    <DefaultContextMenu {...props}>
      {selectedId !== null ? (
        <TldrawUiMenuGroup id="drawdoro-comments">
          <TldrawUiMenuItem
            id="drawdoro-comment"
            label="💬 Comentar"
            icon="chat"
            readonlyOk
            onSelect={handleComment}
          />
        </TldrawUiMenuGroup>
      ) : null}
      <DefaultContextMenuContent />
    </DefaultContextMenu>
  )
}

const components: TLComponents = {
  ContextMenu: CustomContextMenu,
}

export default function DrawingCanvas({ diagram }: DrawingCanvasProps) {
  const saveCanvasState = useAppStore((state) => state.saveCanvasState)
  const setEditor = useAppStore((state) => state.setEditor)
  const isPresentationMode = useAppStore((state) => state.isPresentationMode)

  function handleMount(editor: Editor): () => void {
    setEditor(editor)

    if (diagram.canvas_state !== null) {
      editor.store.loadSnapshot(diagram.canvas_state as unknown as TLStoreSnapshot)
    }

    let timer: ReturnType<typeof setTimeout>
    const unlisten = editor.store.listen(
      () => {
        clearTimeout(timer)
        timer = setTimeout(() => {
          const snapshot = editor.store.getSnapshot()
          void saveCanvasState(snapshot as unknown as CanvasState)
        }, 1500)
      },
      { scope: 'document' },
    )

    return () => {
      clearTimeout(timer)
      unlisten()
      setEditor(null)
    }
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Tldraw
        onMount={handleMount}
        components={components}
        hideUi={isPresentationMode}
        inferDarkMode
      />
      {isPresentationMode ? null : <CommentBadge />}
    </div>
  )
}
