import { Plus } from 'lucide-react'
import { useValue, type Editor } from 'tldraw'

import { createConnectedShape, isConnectable, sidePoint, SIDES, type Side } from '../../utils/connectShapes'

const HANDLE_OFFSET = 20
const DRAG_THRESHOLD = 4

const OUTWARD: Record<Side, { x: number; y: number }> = {
  top: { x: 0, y: -1 },
  right: { x: 1, y: 0 },
  bottom: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
}

interface Handle {
  side: Side
  x: number
  y: number
}

function pointerInfo(editor: Editor, name: 'pointer_down' | 'pointer_move' | 'pointer_up', x: number, y: number, event: PointerEvent | React.PointerEvent) {
  return {
    type: 'pointer' as const,
    name,
    target: 'canvas' as const,
    point: { x, y, z: 0.5 },
    shiftKey: event.shiftKey,
    altKey: event.altKey,
    ctrlKey: event.ctrlKey || event.metaKey,
    metaKey: event.metaKey,
    accelKey: event.metaKey || event.ctrlKey,
    pointerId: event.pointerId,
    button: 0,
    isPen: editor.getInstanceState().isPenMode,
  }
}

// Draw.io-style "+" handles around the selected shape: click to add a connected shape on that
// side, drag to pull an arrow out of that side and drop it on any other shape.
export default function ConnectHandles({ editor }: { editor: Editor }) {
  const handles = useValue<Handle[]>(
    'connect handles',
    () => {
      if (!editor.isIn('select.idle') || editor.getInstanceState().isReadonly) {
        return []
      }
      const shape = editor.getOnlySelectedShape()
      if (!isConnectable(shape) || editor.getZoomLevel() < 0.3) {
        return []
      }
      const bounds = editor.getShapePageBounds(shape)
      if (bounds === undefined) {
        return []
      }
      return SIDES.map((side) => {
        const point = editor.pageToViewport(sidePoint(bounds, side))
        return { side, x: point.x + OUTWARD[side].x * HANDLE_OFFSET, y: point.y + OUTWARD[side].y * HANDLE_OFFSET }
      })
    },
    [editor],
  )

  function handlePointerDown(event: React.PointerEvent, side: Side): void {
    event.preventDefault()
    event.stopPropagation()
    const shape = editor.getOnlySelectedShape()
    const bounds = shape === null ? undefined : editor.getShapePageBounds(shape)
    if (shape === null || bounds === undefined) {
      return
    }
    const startX = event.clientX
    const startY = event.clientY
    let dragging = false

    function handleMove(moveEvent: PointerEvent): void {
      if (!dragging) {
        if (Math.hypot(moveEvent.clientX - startX, moveEvent.clientY - startY) < DRAG_THRESHOLD) {
          return
        }
        dragging = true
        // Start the arrow just inside the shape's edge so tldraw binds it to the source.
        const inward = sidePoint(bounds!, side)
        const origin = editor.pageToScreen({ x: inward.x - OUTWARD[side].x * 2, y: inward.y - OUTWARD[side].y * 2 })
        editor.setCurrentTool('arrow')
        editor.dispatch(pointerInfo(editor, 'pointer_down', origin.x, origin.y, moveEvent))
      }
      editor.dispatch(pointerInfo(editor, 'pointer_move', moveEvent.clientX, moveEvent.clientY, moveEvent))
    }

    function handleUp(upEvent: PointerEvent): void {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', handleUp)
      if (dragging) {
        editor.dispatch(pointerInfo(editor, 'pointer_up', upEvent.clientX, upEvent.clientY, upEvent))
        return
      }
      createConnectedShape(editor, shape!.id, side)
    }

    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', handleUp)
  }

  if (handles.length === 0) {
    return null
  }

  return (
    <div className="connect-layer">
      {handles.map((handle) => (
        <button
          key={handle.side}
          type="button"
          className="connect-handle"
          aria-label={`Add connected shape (${handle.side})`}
          title="Click to add a connected shape · drag to draw an arrow"
          style={{ left: handle.x, top: handle.y }}
          onPointerDown={(event) => handlePointerDown(event, handle.side)}
        >
          <Plus size={12} strokeWidth={2.75} />
        </button>
      ))}
    </div>
  )
}
