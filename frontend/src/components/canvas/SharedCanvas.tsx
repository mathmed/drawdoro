import { useState } from 'react'
import { loadSnapshot, Tldraw, type Editor, type TLComponents, type TLStoreSnapshot } from 'tldraw'
import 'tldraw/tldraw.css'

import type { SharedDiagram } from '../../api/diagrams'
import { useCursorBroadcast } from '../../hooks/useCursorBroadcast'
import { useRealtime, type Presence } from '../../hooks/useRealtime'
import { useThemeStore } from '../../store/useThemeStore'
import { RemoteCursorStore } from '../../utils/remoteCursors'
import RemoteCursorsLayer from '../presence/RemoteCursorsLayer'
import { RemoteCursorsContext } from '../presence/RemoteCursorsContext'
import CanvasLoadingScreen from '../ui/loading/CanvasLoadingScreen'
import { shapeUtils } from './shapeUtils'

interface SharedCanvasProps {
  diagram: SharedDiagram
  shareToken: string
  guestName?: string
}

// Guests never edit, so tldraw's editing chrome is hidden entirely.
const components: TLComponents = {
  StylePanel: null,
  Toolbar: null,
  QuickActions: null,
  ActionsMenu: null,
  MainMenu: null,
  PageMenu: null,
  LoadingScreen: CanvasLoadingScreen,
  InFrontOfTheCanvas: RemoteCursorsLayer,
}

export default function SharedCanvas({ diagram, shareToken, guestName }: SharedCanvasProps) {
  const [editor, setEditor] = useState<Editor | null>(null)
  const theme = useThemeStore((state) => state.resolved)

  // Live updates from editors flow in; the read-only viewer only receives them. Pointers go both
  // ways, like the presence: editors see the guest's cursor and the guest sees theirs.
  const noop = (_: Presence): void => undefined
  const [remoteCursors] = useState(() => new RemoteCursorStore())
  const { sendCursor } = useRealtime({
    diagramId: diagram.id,
    editor,
    onPresenceChange: noop,
    shareToken,
    guestName,
    remoteCursors,
  })
  useCursorBroadcast(editor, sendCursor)

  function handleMount(mountedEditor: Editor): void {
    setEditor(mountedEditor)
    mountedEditor.user.updateUserPreferences({ colorScheme: theme, locale: 'en' })
    if (diagram.canvas_state !== null) {
      loadSnapshot(mountedEditor.store, diagram.canvas_state as unknown as TLStoreSnapshot)
    }
    mountedEditor.updateInstanceState({ isReadonly: true })
    mountedEditor.zoomToFit()
  }

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <RemoteCursorsContext.Provider value={remoteCursors}>
        <Tldraw onMount={handleMount} components={components} shapeUtils={shapeUtils} />
      </RemoteCursorsContext.Provider>
    </div>
  )
}
