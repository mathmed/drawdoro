import type { Editor, TLShape, TLShapeId } from 'tldraw'

import type { ShapeMetadata } from '../api/types'

export type SelectionCommand = 'connected' | 'arrows' | 'matching' | 'invert'

function topLevelShapes(editor: Editor): TLShape[] {
  return editor.getCurrentPageShapes().filter((shape) => shape.parentId.startsWith('page:'))
}

function arrowEnds(editor: Editor, arrowId: TLShapeId): TLShapeId[] {
  return editor
    .getBindingsFromShape(arrowId, 'arrow')
    .map((binding) => binding.toId)
}

// One hop per call: repeating the command keeps expanding the neighbourhood.
function connectedShapeIds(editor: Editor): TLShapeId[] {
  const result = new Set(editor.getSelectedShapeIds())
  for (const id of editor.getSelectedShapeIds()) {
    const shape = editor.getShape(id)
    if (shape === undefined) {
      continue
    }
    if (shape.type === 'arrow') {
      arrowEnds(editor, id).forEach((endId) => result.add(endId))
      continue
    }
    for (const binding of editor.getBindingsToShape(id, 'arrow')) {
      result.add(binding.fromId)
      arrowEnds(editor, binding.fromId).forEach((endId) => result.add(endId))
    }
  }
  return [...result]
}

function kindOf(shape: TLShape, metadata: Record<string, ShapeMetadata>): string {
  const semanticType = metadata[shape.id]?.type
  if (semanticType !== undefined) {
    return `semantic:${semanticType}`
  }
  const geo = (shape.props as { geo?: string }).geo
  return geo === undefined ? shape.type : `${shape.type}:${geo}`
}

function matchingShapeIds(editor: Editor, metadata: Record<string, ShapeMetadata>): TLShapeId[] {
  const kinds = new Set(editor.getSelectedShapes().map((shape) => kindOf(shape, metadata)))
  return topLevelShapes(editor)
    .filter((shape) => kinds.has(kindOf(shape, metadata)))
    .map((shape) => shape.id)
}

export function canRunSelection(command: SelectionCommand, editor: Editor): boolean {
  const hasSelection = editor.getSelectedShapeIds().length > 0
  if (command === 'connected' || command === 'matching') {
    return hasSelection
  }
  return topLevelShapes(editor).length > 0
}

export function runSelection(
  command: SelectionCommand,
  editor: Editor,
  metadata: Record<string, ShapeMetadata>,
): number {
  if (!canRunSelection(command, editor)) {
    return 0
  }
  let ids: TLShapeId[]
  if (command === 'connected') {
    ids = connectedShapeIds(editor)
  } else if (command === 'matching') {
    ids = matchingShapeIds(editor, metadata)
  } else if (command === 'arrows') {
    ids = topLevelShapes(editor)
      .filter((shape) => shape.type === 'arrow')
      .map((shape) => shape.id)
  } else {
    const selected = new Set(editor.getSelectedShapeIds())
    ids = topLevelShapes(editor)
      .filter((shape) => !selected.has(shape.id))
      .map((shape) => shape.id)
  }
  editor.setCurrentTool('select')
  editor.setSelectedShapes(ids)
  return ids.length
}

export const SELECTION_COMMANDS: { command: SelectionCommand; label: string; code: string; kbd: string; hint: string }[] = [
  { command: 'connected', label: 'Select connected', code: 'KeyC', kbd: '?c', hint: '⌥C' },
  { command: 'arrows', label: 'Select all connections', code: 'KeyE', kbd: '?e', hint: '⌥E' },
  { command: 'matching', label: 'Select same type', code: 'KeyM', kbd: '?m', hint: '⌥M' },
  { command: 'invert', label: 'Invert selection', code: 'KeyI', kbd: '?i', hint: '⌥I' },
]
