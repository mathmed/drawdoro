import { useState } from 'react'
import {
  ArrowShapeUtil,
  loadSnapshot,
  Tldraw,
  type Editor,
  type TLComponents,
  type TLStoreSnapshot,
} from 'tldraw'
import 'tldraw/tldraw.css'

import type { SharedDiagram } from '../../api/diagrams'
import { useRealtime, type Presence } from '../../hooks/useRealtime'
import { useThemeStore } from '../../store/useThemeStore'
import { DrawdoroGeoShapeUtil } from '../../shapes/DrawdoroGeoShapeUtil'

interface SharedCanvasProps {
  diagram: SharedDiagram
  shareToken: string
  guestName?: string
}

const shapeUtils = [
  DrawdoroGeoShapeUtil,
  ArrowShapeUtil.configure({
    elbowArrowPointSnapDistance: 36,
    elbowArrowEdgeSnapDistance: 28,
    elbowArrowCenterSnapDistance: 32,
    arcArrowCenterSnapDistance: 24,
  }),
]

// Guests never edit, so tldraw's editing chrome is hidden entirely.
const components: TLComponents = {
  StylePanel: null,
  Toolbar: null,
  QuickActions: null,
  ActionsMenu: null,
  MainMenu: null,
  PageMenu: null,
}

export default function SharedCanvas({ diagram, shareToken, guestName }: SharedCanvasProps) {
  const [editor, setEditor] = useState<Editor | null>(null)
  const theme = useThemeStore((state) => state.resolved)

  // Live updates from editors flow in; the read-only viewer only receives them.
  const noop = (_: Presence): void => undefined
  useRealtime({ diagramId: diagram.id, editor, onPresenceChange: noop, shareToken, guestName })

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
      <Tldraw onMount={handleMount} components={components} shapeUtils={shapeUtils} />
    </div>
  )
}
