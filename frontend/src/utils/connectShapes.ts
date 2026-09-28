import {
  ArrowShapeKindStyle,
  createShapeId,
  toRichText,
  type Box,
  type Editor,
  type TLShape,
  type TLShapeId,
  type VecModel,
} from 'tldraw'

export type Side = 'top' | 'right' | 'bottom' | 'left'

export const SIDES: Side[] = ['top', 'right', 'bottom', 'left']

const GAP = 96
const CONNECTABLE_TYPES = new Set(['geo', 'note'])

const OPPOSITE: Record<Side, Side> = { top: 'bottom', right: 'left', bottom: 'top', left: 'right' }

const ANCHOR: Record<Side, VecModel> = {
  top: { x: 0.5, y: 0 },
  right: { x: 1, y: 0.5 },
  bottom: { x: 0.5, y: 1 },
  left: { x: 0, y: 0.5 },
}

export function isConnectable(shape: TLShape | null | undefined): shape is TLShape {
  return shape != null && CONNECTABLE_TYPES.has(shape.type) && !shape.isLocked
}

export function sidePoint(bounds: Box, side: Side): VecModel {
  const anchor = ANCHOR[side]
  return { x: bounds.x + bounds.w * anchor.x, y: bounds.y + bounds.h * anchor.y }
}

function offsetFor(bounds: Box, side: Side, step: number): VecModel {
  const dx = (bounds.w + GAP) * step
  const dy = (bounds.h + GAP) * step
  return { top: { x: 0, y: -dy }, right: { x: dx, y: 0 }, bottom: { x: 0, y: dy }, left: { x: -dx, y: 0 } }[side]
}

// Walks further in the chosen direction until the new shape would not overlap anything.
function freeOffset(editor: Editor, source: TLShape, bounds: Box, side: Side): VecModel {
  const others = editor
    .getCurrentPageShapes()
    .filter((shape) => shape.id !== source.id && shape.type !== 'arrow')
    .map((shape) => editor.getShapePageBounds(shape))
    .filter((box): box is Box => box !== undefined)
  for (let step = 1; step <= 6; step++) {
    const offset = offsetFor(bounds, side, step)
    const candidate = bounds.clone().translate(offset)
    if (!others.some((box) => box.collides(candidate))) {
      return offset
    }
  }
  return offsetFor(bounds, side, 1)
}

export function connectArrow(editor: Editor, fromId: TLShapeId, fromSide: Side, toId: TLShapeId, toSide: Side): void {
  const from = editor.getShapePageBounds(fromId)
  const to = editor.getShapePageBounds(toId)
  if (from === undefined || to === undefined) {
    return
  }
  const start = sidePoint(from, fromSide)
  const end = sidePoint(to, toSide)
  const arrowId = createShapeId()
  editor.createShape({
    id: arrowId,
    type: 'arrow',
    x: start.x,
    y: start.y,
    props: {
      kind: editor.getStyleForNextShape(ArrowShapeKindStyle),
      start: { x: 0, y: 0 },
      end: { x: end.x - start.x, y: end.y - start.y },
    },
  })
  const binding = { isExact: false, isPrecise: true, snap: 'edge-point' as const }
  editor.createBindings([
    { type: 'arrow', fromId: arrowId, toId: fromId, props: { ...binding, terminal: 'start', normalizedAnchor: ANCHOR[fromSide] } },
    { type: 'arrow', fromId: arrowId, toId, props: { ...binding, terminal: 'end', normalizedAnchor: ANCHOR[toSide] } },
  ])
}

// Flowchart-style quick connect: clone the shape on the given side, link both with an arrow
// and start editing the new shape's label so the user can type right away.
export function createConnectedShape(editor: Editor, sourceId: TLShapeId, side: Side): TLShapeId | null {
  const source = editor.getShape(sourceId)
  const bounds = editor.getShapePageBounds(sourceId)
  if (!isConnectable(source) || bounds === undefined) {
    return null
  }
  const offset = freeOffset(editor, source, bounds, side)
  const newId = createShapeId()
  editor.markHistoryStoppingPoint('quick connect')
  editor.run(() => {
    editor.createShape({
      id: newId,
      type: source.type,
      parentId: source.parentId,
      x: source.x + offset.x,
      y: source.y + offset.y,
      rotation: source.rotation,
      meta: source.meta,
      props: { ...source.props, richText: toRichText('') },
    })
    connectArrow(editor, sourceId, side, newId, OPPOSITE[side])
  })
  editor.setCurrentTool('select')
  editor.select(newId)
  editor.setEditingShape(newId)
  editor.setCurrentTool('select.editing_shape')
  return newId
}
