import type { Editor, TLShapeId } from 'tldraw'

import { canSaveSelection } from './gallery'
import { canRunSelection, SELECTION_COMMANDS, type SelectionCommand } from './shapeSelection'

export interface ContextMenuSelection {
  commentTargetId: TLShapeId | null
  canSaveToGallery: boolean
  selectionCommands: SelectionCommand[]
}

// Same rules as the command palette, so both entry points always offer the same actions.
export function getContextMenuSelection(editor: Editor): ContextMenuSelection {
  return {
    commentTargetId: editor.getOnlySelectedShapeId(),
    canSaveToGallery: canSaveSelection(editor),
    selectionCommands: SELECTION_COMMANDS.filter(({ command }) => canRunSelection(command, editor)).map(
      ({ command }) => command,
    ),
  }
}
