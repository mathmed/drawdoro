import type { Editor } from 'tldraw'
import { describe, expect, it } from 'vitest'

import { getContextMenuSelection } from './contextMenu'
import { canSaveSelection } from './gallery'

function fakeEditor(selected: string[], shapes: string[]): Editor {
  return {
    getSelectedShapeIds: () => selected,
    getOnlySelectedShapeId: () => (selected.length === 1 ? selected[0] : null),
    getCurrentPageShapes: () => shapes.map((id) => ({ id, parentId: 'page:page' })),
  } as unknown as Editor
}

describe('getContextMenuSelection', () => {
  it('should offer only page-wide commands on an empty selection', () => {
    const sut = getContextMenuSelection(fakeEditor([], ['shape:a', 'shape:b']))

    expect(sut).toEqual({ commentTargetId: null, canSaveToGallery: false, selectionCommands: ['arrows', 'invert'] })
  })

  it('should offer comment, save to gallery and every command for a single shape', () => {
    const sut = getContextMenuSelection(fakeEditor(['shape:a'], ['shape:a', 'shape:b']))

    expect(sut).toEqual({
      commentTargetId: 'shape:a',
      canSaveToGallery: true,
      selectionCommands: ['connected', 'arrows', 'matching', 'invert'],
    })
  })

  it('should offer save to gallery but no comment for a multiple selection', () => {
    const sut = getContextMenuSelection(fakeEditor(['shape:a', 'shape:b'], ['shape:a', 'shape:b']))

    expect(sut.commentTargetId).toBeNull()
    expect(sut.canSaveToGallery).toBe(true)
  })

  it('should follow the same save rule as the command palette', () => {
    for (const selected of [[], ['shape:a'], ['shape:a', 'shape:b']]) {
      const editor = fakeEditor(selected, ['shape:a', 'shape:b'])

      expect(getContextMenuSelection(editor).canSaveToGallery).toBe(canSaveSelection(editor))
    }
  })

  it('should offer nothing on an empty page', () => {
    const sut = getContextMenuSelection(fakeEditor([], []))

    expect(sut).toEqual({ commentTargetId: null, canSaveToGallery: false, selectionCommands: [] })
  })
})
