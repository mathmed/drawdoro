import { useEffect } from 'react'
import {
  ArrowShapeKindStyle,
  DefaultContextMenu,
  DefaultContextMenuContent,
  loadSnapshot,
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
import { useRealtime } from '../../hooks/useRealtime'
import { useSelectionShortcuts } from '../../hooks/useSelectionShortcuts'
import { useAppStore } from '../../store/useAppStore'
import { useThemeStore } from '../../store/useThemeStore'
import { registerGeoDefaults } from '../../shapes/CustomGeoShapeUtil'
import { canRunSelection, runSelection, SELECTION_COMMANDS } from '../../utils/shapeSelection'
import CommentBadge from '../comments/CommentBadge'
import ConnectHandles from './ConnectHandles'
import StylePanel, { MenuPanelWithStyles } from './StylePanel'
import RichTextToolbar, { textOptions } from './RichTextToolbar'
import { shapeUtils } from './shapeUtils'
import Toolbar, { toolOverrides } from './Toolbar'

interface DrawingCanvasProps {
  diagram: Diagram
}

function CustomContextMenu(props: TLUiContextMenuProps) {
  const editor = useEditor()
  const commentOnElement = useAppStore((state) => state.commentOnElement)
  const selectedId = editor.getOnlySelectedShapeId()

  function handleComment(): void {
    if (selectedId !== null) {
      commentOnElement(selectedId)
    }
  }

  return (
    <DefaultContextMenu {...props}>
      {selectedId !== null ? (
        <TldrawUiMenuGroup id="app-comments">
          <TldrawUiMenuItem
            id="app-comment"
            label="Comment"
            icon="chat"
            readonlyOk
            onSelect={handleComment}
          />
        </TldrawUiMenuGroup>
      ) : null}
      <TldrawUiMenuGroup id="app-select">
        {SELECTION_COMMANDS.filter(({ command }) => canRunSelection(command, editor)).map((entry) => (
          <TldrawUiMenuItem
            key={entry.command}
            id={`app-select-${entry.command}`}
            label={entry.label}
            kbd={entry.kbd}
            readonlyOk
            onSelect={() => {
              runSelection(entry.command, editor, useAppStore.getState().semanticMetadata)
            }}
          />
        ))}
      </TldrawUiMenuGroup>
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
      setEditor(null)
    }
  }

  return (
    <div
      style={{ width: '100%', height: '100%', position: 'relative' }}
      onPointerDownCapture={() => editor?.focus()}
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
