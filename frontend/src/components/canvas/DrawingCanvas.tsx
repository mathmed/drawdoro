import { useEffect, type DragEvent } from 'react'
import {
  ArrowShapeKindStyle,
  DefaultContextMenu,
  DefaultContextMenuContent,
  loadSnapshot,
  Tldraw,
  type Editor,
  type TLComponents,
  type TLStoreSnapshot,
  type TLUiContextMenuProps,
} from 'tldraw'
import 'tldraw/tldraw.css'

import type { CanvasState, Diagram } from '../../api/types'
import { useRealtime } from '../../hooks/useRealtime'
import { useSelectionShortcuts } from '../../hooks/useSelectionShortcuts'
import { useAppStore } from '../../store/useAppStore'
import { useThemeStore } from '../../store/useThemeStore'
import { registerGeoDefaults } from '../../shapes/CustomGeoShapeUtil'
import { registerSloppinessDefaults } from '../../shapes/sloppiness'
import { GALLERY_DRAG_TYPE, insertGalleryItem } from '../../utils/gallery'
import CommentBadge from '../comments/CommentBadge'
import AppContextMenuItems from './AppContextMenuItems'
import ConnectHandles from './ConnectHandles'
import StylePanel, { MenuPanelWithStyles } from './StylePanel'
import RichTextToolbar, { textOptions } from './RichTextToolbar'
import { shapeUtils } from './shapeUtils'
import Toolbar, { toolOverrides } from './Toolbar'

interface DrawingCanvasProps {
  diagram: Diagram
}

function CustomContextMenu(props: TLUiContextMenuProps) {
  return (
    <DefaultContextMenu {...props}>
      <AppContextMenuItems />
      <DefaultContextMenuContent />
    </DefaultContextMenu>
  )
}

const components: TLComponents = {
  ContextMenu: CustomContextMenu,
  StylePanel,
  MenuPanel: MenuPanelWithStyles,
  Toolbar,
  RichTextToolbar,
}

export default function DrawingCanvas({ diagram }: DrawingCanvasProps) {
  const saveCanvasState = useAppStore((state) => state.saveCanvasState)
  const setEditor = useAppStore((state) => state.setEditor)
  const isPresentationMode = useAppStore((state) => state.isPresentationMode)
  const editor = useAppStore((state) => state.editor)
  const setPresence = useAppStore((state) => state.setPresence)
  const applyPushedDiagram = useAppStore((state) => state.applyPushedDiagram)
  const theme = useThemeStore((state) => state.resolved)

  useSelectionShortcuts(editor)

  useEffect(() => {
    editor?.user.updateUserPreferences({ colorScheme: theme })
  }, [editor, theme])

  // Viewers get a read-only canvas: they can pan, zoom and select but not change shapes.
  const isViewer = useAppStore((state) => state.myRole === 'viewer')
  useEffect(() => {
    editor?.updateInstanceState({ isReadonly: isViewer })
  }, [editor, isViewer])

  const { sendUpdate } = useRealtime({
    diagramId: diagram.id,
    editor,
    onPresenceChange: setPresence,
    onDiagramPushed: applyPushedDiagram,
  })

  function handleMount(mountedEditor: Editor): () => void {
    setEditor(mountedEditor)
    // tldraw follows the browser language by default; pin it so its menus match the app's English UI.
    // isPasteAtCursorMode makes Ctrl/Cmd+V drop the pasted shapes at the pointer instead of on top
    // of the originals; tldraw falls back to the last known pointer position when it left the canvas.
    mountedEditor.user.updateUserPreferences({
      colorScheme: useThemeStore.getState().resolved,
      locale: 'en',
      isPasteAtCursorMode: true,
    })

    if (diagram.canvas_state !== null) {
      // store.loadSnapshot would also wipe the session record (focus, tool state), which left
      // the editor unfocused and every tldraw keyboard shortcut dead.
      loadSnapshot(mountedEditor.store, diagram.canvas_state as unknown as TLStoreSnapshot)
    }
    mountedEditor.setStyleForNextShapes(ArrowShapeKindStyle, 'elbow')
    const unregisterGeoDefaults = registerGeoDefaults(mountedEditor)
    const unregisterSloppinessDefaults = registerSloppinessDefaults(mountedEditor)
    mountedEditor.focus()

    let timer: ReturnType<typeof setTimeout>
    const unlisten = mountedEditor.store.listen(
      (entry) => {
        // Changes coming from other peers are already persisted by them.
        if (entry.source === 'remote') {
          return
        }
        clearTimeout(timer)
        timer = setTimeout(() => {
          const snapshot = mountedEditor.store.getSnapshot()
          void saveCanvasState(snapshot as unknown as CanvasState)
          sendUpdate(snapshot)
        }, 500)
      },
      { scope: 'document' },
    )

    return () => {
      clearTimeout(timer)
      unlisten()
      unregisterGeoDefaults()
      unregisterSloppinessDefaults()
      setEditor(null)
    }
  }

  // Gallery tiles are dragged in with their own dataTransfer type; everything else (files, urls)
  // keeps going to tldraw's own drop handler.
  function handleDragOverCapture(event: DragEvent): void {
    if (event.dataTransfer.types.includes(GALLERY_DRAG_TYPE)) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'copy'
    }
  }

  function handleDropCapture(event: DragEvent): void {
    const itemId = event.dataTransfer.getData(GALLERY_DRAG_TYPE)
    if (itemId === '' || editor === null) {
      return
    }
    event.preventDefault()
    event.stopPropagation()
    void insertGalleryItem(editor, itemId, editor.screenToPage({ x: event.clientX, y: event.clientY }))
  }

  return (
    <div
      style={{ width: '100%', height: '100%', position: 'relative' }}
      onPointerDownCapture={() => editor?.focus()}
      onDragOverCapture={handleDragOverCapture}
      onDropCapture={handleDropCapture}
    >
      <Tldraw
        onMount={handleMount}
        components={components}
        shapeUtils={shapeUtils}
        overrides={toolOverrides}
        textOptions={textOptions}
        hideUi={isPresentationMode}
      />
      {isPresentationMode || editor === null ? null : <ConnectHandles editor={editor} />}
      {isPresentationMode ? null : <CommentBadge />}
    </div>
  )
}
