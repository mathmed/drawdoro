import { atom } from '@tldraw/state'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import type { Editor } from 'tldraw'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAppStore } from '../../store/useAppStore'
import { saveSelectionToGallery } from '../../utils/gallery'
import AppContextMenuItems from './AppContextMenuItems'

const fake = vi.hoisted(() => ({ editor: null as unknown }))

// The real reactive useValue, so the test fails if the menu goes back to plain reads in render.
vi.mock('tldraw', async () => {
  const { useValue } = await import('@tldraw/state-react')
  return {
    useValue,
    useEditor: () => fake.editor,
    TldrawUiMenuGroup: ({ children }: { children: ReactNode }) => <div role="group">{children}</div>,
    TldrawUiMenuItem: ({ label, onSelect }: { label: string; onSelect: () => void }) => (
      <button type="button" role="menuitem" onClick={onSelect}>
        {label}
      </button>
    ),
  }
})
vi.mock('../../utils/gallery', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../utils/gallery')>()),
  saveSelectionToGallery: vi.fn(),
}))

const selection = atom<string[]>('selection', [])

function createEditor(): Editor {
  return {
    getSelectedShapeIds: () => selection.get(),
    getOnlySelectedShapeId: () => {
      const ids = selection.get()
      return ids.length === 1 ? ids[0] : null
    },
    getCurrentPageShapes: () => [
      { id: 'shape:a', parentId: 'page:page' },
      { id: 'shape:b', parentId: 'page:page' },
    ],
  } as unknown as Editor
}

function renderSut() {
  return render(<AppContextMenuItems />)
}

function labels(): string[] {
  return screen.queryAllByRole('menuitem').map((item) => item.textContent ?? '')
}

beforeEach(() => {
  selection.set([])
  fake.editor = createEditor()
  useAppStore.setState(useAppStore.getInitialState(), true)
})

describe('AppContextMenuItems', () => {
  it('should offer save to gallery when shapes are selected', () => {
    selection.set(['shape:a'])

    renderSut()

    expect(labels()).toContain('Save to gallery')
  })

  it('should not offer save to gallery nor comment without a selection', () => {
    renderSut()

    expect(labels()).toEqual(['Select all connections', 'Invert selection'])
  })

  it('should react to a selection change after the first render', () => {
    renderSut()
    expect(labels()).not.toContain('Save to gallery')

    act(() => selection.set(['shape:a']))

    expect(labels()).toContain('Save to gallery')
    expect(labels()).toContain('Comment')

    act(() => selection.set(['shape:a', 'shape:b']))

    expect(labels()).toContain('Save to gallery')
    expect(labels()).not.toContain('Comment')
  })

  it('should reflect the current selection each time the menu opens', () => {
    selection.set(['shape:a'])
    const first = renderSut()
    expect(labels()).toContain('Comment')
    first.unmount()

    selection.set([])
    renderSut()

    expect(labels()).not.toContain('Comment')
    expect(labels()).not.toContain('Save to gallery')
  })

  it('should save the current selection to the gallery', async () => {
    selection.set(['shape:a'])
    renderSut()

    await userEvent.click(screen.getByRole('menuitem', { name: 'Save to gallery' }))

    expect(saveSelectionToGallery).toHaveBeenCalledWith(fake.editor)
  })

  it('should comment on the shape selected when the menu opened', async () => {
    const commentOnElement = vi.fn()
    useAppStore.setState({ commentOnElement })
    selection.set(['shape:b'])
    renderSut()

    await userEvent.click(screen.getByRole('menuitem', { name: 'Comment' }))

    expect(commentOnElement).toHaveBeenCalledWith('shape:b')
  })
})
