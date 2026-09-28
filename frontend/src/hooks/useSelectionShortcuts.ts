import { useEffect } from 'react'
import type { Editor } from 'tldraw'

import { useAppStore } from '../store/useAppStore'
import { toast } from '../store/useToastStore'
import { createConnectedShape, isConnectable, type Side } from '../utils/connectShapes'
import { runSelection, SELECTION_COMMANDS } from '../utils/shapeSelection'

const ARROW_SIDES: Record<string, Side> = { ArrowUp: 'top', ArrowRight: 'right', ArrowDown: 'bottom', ArrowLeft: 'left' }

function canHandle(editor: Editor): boolean {
  return (
    editor.getInstanceState().isFocused &&
    editor.getEditingShapeId() === null &&
    !editor.getIsMenuOpen() &&
    editor.isIn('select.idle')
  )
}

// Complements tldraw's own selection keys (Tab, ⌘+arrows, ⌘A, Esc). Listeners run in the
// capture phase so tldraw, which listens on its container, never sees the keys we consume.
export function useSelectionShortcuts(editor: Editor | null): void {
  useEffect(() => {
    if (editor === null) {
      return
    }
    const activeEditor = editor
    let swallowTabKeyUp = false

    function handleKeyDown(event: KeyboardEvent): void {
      if (!canHandle(activeEditor) || event.metaKey || event.ctrlKey) {
        return
      }

      // tldraw ignores Tab until something is selected (and lets focus leave the canvas),
      // so the first Tab picks the first shape in reading order, Shift+Tab the last one.
      if (event.key === 'Tab' && !event.altKey && activeEditor.getSelectedShapeIds().length === 0) {
        event.preventDefault()
        event.stopPropagation()
        swallowTabKeyUp = true
        activeEditor.selectAdjacentShape(event.shiftKey ? 'prev' : 'next')
        return
      }

      // ⌥⇧+arrow: Excalidraw-style flowchart, add a connected shape in that direction.
      const side = ARROW_SIDES[event.key]
      if (event.altKey && event.shiftKey && side !== undefined) {
        const shape = activeEditor.getOnlySelectedShape()
        if (isConnectable(shape)) {
          event.preventDefault()
          event.stopPropagation()
          createConnectedShape(activeEditor, shape.id, side)
        }
        return
      }

      if (!event.altKey || event.shiftKey) {
        return
      }
      const entry = SELECTION_COMMANDS.find((item) => item.code === event.code)
      if (entry === undefined) {
        return
      }
      event.preventDefault()
      event.stopPropagation()
      const count = runSelection(entry.command, activeEditor, useAppStore.getState().semanticMetadata)
      if (count === 0) {
        toast(
          entry.command === 'connected' || entry.command === 'matching'
            ? 'Select a shape first.'
            : 'Nothing to select.',
          'info',
        )
      }
    }

    // Without this, tldraw's own Tab-on-keyup would immediately advance past the first shape.
    function handleKeyUp(event: KeyboardEvent): void {
      if (event.key === 'Tab' && swallowTabKeyUp) {
        swallowTabKeyUp = false
        event.stopPropagation()
      }
    }

    window.addEventListener('keydown', handleKeyDown, true)
    window.addEventListener('keyup', handleKeyUp, true)
    return () => {
      window.removeEventListener('keydown', handleKeyDown, true)
      window.removeEventListener('keyup', handleKeyUp, true)
    }
  }, [editor])
}
