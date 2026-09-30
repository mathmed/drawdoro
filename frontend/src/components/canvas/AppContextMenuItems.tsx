import { TldrawUiMenuGroup, TldrawUiMenuItem, useEditor, useValue } from 'tldraw'

import { useAppStore } from '../../store/useAppStore'
import { getContextMenuSelection } from '../../utils/contextMenu'
import { saveSelectionToGallery } from '../../utils/gallery'
import { runSelection, SELECTION_COMMANDS } from '../../utils/shapeSelection'

// Reads the selection through useValue: a plain read during render keeps whatever the selection was
// the first time the menu rendered.
export default function AppContextMenuItems() {
  const editor = useEditor()
  const commentOnElement = useAppStore((state) => state.commentOnElement)
  const { commentTargetId, canSaveToGallery, selectionCommands } = useValue(
    'app context menu selection',
    () => getContextMenuSelection(editor),
    [editor],
  )
  const commands = SELECTION_COMMANDS.filter(({ command }) => selectionCommands.includes(command))

  return (
    <>
      {commentTargetId !== null ? (
        <TldrawUiMenuGroup id="app-comments">
          <TldrawUiMenuItem
            id="app-comment"
            label="Comment"
            icon="chat"
            readonlyOk
            onSelect={() => commentOnElement(commentTargetId)}
          />
        </TldrawUiMenuGroup>
      ) : null}
      {canSaveToGallery ? (
        <TldrawUiMenuGroup id="app-gallery">
          <TldrawUiMenuItem
            id="app-save-to-gallery"
            label="Save to gallery"
            icon="bookmark"
            readonlyOk
            onSelect={() => void saveSelectionToGallery(editor)}
          />
        </TldrawUiMenuGroup>
      ) : null}
      {commands.length > 0 ? (
        <TldrawUiMenuGroup id="app-select">
          {commands.map((entry) => (
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
      ) : null}
    </>
  )
}
