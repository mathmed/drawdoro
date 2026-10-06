import { Box, loadSnapshot, Tldraw, type Editor, type TLShapeId, type TLStoreSnapshot } from 'tldraw'
import 'tldraw/tldraw.css'

import { textOptions } from '../components/canvas/textOptions'
import { shapeUtils } from '../components/canvas/shapeUtils'
import { blobToBase64 } from '../utils/blob'

interface RenderRegion {
  x: number
  y: number
  width: number
  height: number
}

interface RenderRequest {
  shape_ids: string[] | null
  region: RenderRegion | null
  max_size: number
}

declare global {
  interface Window {
    // Called by the MCP server's headless browser (render_diagram); resolves to a base64 PNG.
    renderDiagram?: (snapshot: TLStoreSnapshot, request: RenderRequest) => Promise<string>
  }
}

function exportBounds(editor: Editor, ids: TLShapeId[], region: RenderRegion | null): Box | null {
  if (region !== null) {
    return new Box(region.x, region.y, region.width, region.height)
  }
  const boxes = ids.map((id) => editor.getShapePageBounds(id)).filter((box) => box !== undefined)
  return boxes.length === 0 ? null : Box.Common(boxes)
}

async function render(editor: Editor, snapshot: TLStoreSnapshot, request: RenderRequest): Promise<string> {
  loadSnapshot(editor.store, snapshot)
  // Text measured before its font arrives comes out too narrow and wraps in the export.
  await editor.fonts.loadRequiredFontsForCurrentPage()
  const pageShapeIds = editor.getCurrentPageShapeIds()
  const ids =
    request.shape_ids === null
      ? [...pageShapeIds]
      : (request.shape_ids as TLShapeId[]).filter((id) => pageShapeIds.has(id))
  const bounds = exportBounds(editor, ids, request.region)
  if (ids.length === 0 || bounds === null) {
    throw new Error('Nothing to render: the diagram or the requested shapes are empty')
  }
  // Big canvases shrink until their longest side fits max_size; small ones are never enlarged.
  const scale = Math.min(1, request.max_size / Math.max(bounds.w, bounds.h))
  const { blob } = await editor.toImage(ids, {
    format: 'png',
    background: true,
    bounds,
    scale,
    pixelRatio: 1,
    padding: request.region === null ? 16 : 0,
    darkMode: false,
  })
  return blobToBase64(blob)
}

// Headless page for render_diagram: no UI, no API calls. The canvas arrives from the caller, so the
// page is public without exposing any diagram.
export default function RenderDiagramPage() {
  function handleMount(editor: Editor): () => void {
    editor.user.updateUserPreferences({ colorScheme: 'light', locale: 'en' })
    window.renderDiagram = (snapshot, request) => render(editor, snapshot, request)
    return () => {
      window.renderDiagram = undefined
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0 }}>
      <Tldraw hideUi onMount={handleMount} shapeUtils={shapeUtils} textOptions={textOptions} />
    </div>
  )
}
