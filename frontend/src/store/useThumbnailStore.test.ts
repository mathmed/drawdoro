import type { Editor } from 'tldraw'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listDiagramThumbnails, saveDiagramThumbnail } from '../api/diagrams'
import type { DiagramThumbnail } from '../api/types'
import { renderDiagramThumbnails } from '../utils/diagramThumbnail'
import { projectKey, useThumbnailStore } from './useThumbnailStore'

vi.mock('../api/diagrams', () => ({ listDiagramThumbnails: vi.fn(), saveDiagramThumbnail: vi.fn() }))
vi.mock('../utils/diagramThumbnail', () => ({ renderDiagramThumbnails: vi.fn() }))

const EDITOR = {} as Editor
const TARGET = { projectId: 'p1', diagramId: 'd1', version: '2026-10-06T12:00:00.5' }

function listed(overrides: Partial<DiagramThumbnail> = {}): DiagramThumbnail {
  return { diagram_id: 'd1', version: '2026-10-06T12:00:00', mime_type: 'image/webp', image_base64: 'AAAA', ...overrides }
}

function items(theme: 'light' | 'dark', projectId = 'p1') {
  return useThumbnailStore.getState().byProject[projectKey(theme, projectId)]
}

beforeEach(() => {
  useThumbnailStore.setState(useThumbnailStore.getInitialState(), true)
})

describe('useThumbnailStore.load', () => {
  it('should keep the project previews of the theme as data URLs', async () => {
    vi.mocked(listDiagramThumbnails).mockResolvedValue([listed()])

    await useThumbnailStore.getState().load('p1', 'dark')

    expect(listDiagramThumbnails).toHaveBeenCalledWith('p1', 'dark')
    expect(items('dark')).toEqual({
      loaded: true,
      items: { d1: { src: 'data:image/webp;base64,AAAA', version: '2026-10-06T12:00:00' } },
    })
    expect(items('light')).toBeUndefined()
  })

  it('should replace the previews of an earlier visit', async () => {
    vi.mocked(listDiagramThumbnails).mockResolvedValueOnce([listed(), listed({ diagram_id: 'd2' })])
    await useThumbnailStore.getState().load('p1', 'light')
    vi.mocked(listDiagramThumbnails).mockResolvedValueOnce([listed({ diagram_id: 'd2' })])

    await useThumbnailStore.getState().load('p1', 'light')

    expect(Object.keys(items('light').items)).toEqual(['d2'])
  })

  it('should keep a preview this tab stored that is newer than the listed one', async () => {
    vi.mocked(renderDiagramThumbnails).mockResolvedValue({ light: { base64: 'NEW', mimeType: 'image/png' }, dark: null })
    vi.mocked(saveDiagramThumbnail).mockResolvedValue()
    await useThumbnailStore.getState().capture(EDITOR, TARGET)
    vi.mocked(listDiagramThumbnails).mockResolvedValue([listed()])

    await useThumbnailStore.getState().load('p1', 'light')

    expect(items('light').items.d1).toEqual({ src: 'data:image/png;base64,NEW', version: TARGET.version })
  })

  it('should take the listed preview when it is newer than the one this tab stored', async () => {
    vi.mocked(renderDiagramThumbnails).mockResolvedValue({ light: { base64: 'OLD', mimeType: 'image/png' }, dark: null })
    vi.mocked(saveDiagramThumbnail).mockResolvedValue()
    await useThumbnailStore.getState().capture(EDITOR, { ...TARGET, version: '2026-10-06T11:00:00' })
    vi.mocked(listDiagramThumbnails).mockResolvedValue([listed()])

    await useThumbnailStore.getState().load('p1', 'light')

    expect(items('light').items.d1.src).toBe('data:image/webp;base64,AAAA')
  })

  it('should mark the project loaded when the request fails, so cards show their placeholder', async () => {
    vi.mocked(listDiagramThumbnails).mockRejectedValue(new Error('offline'))

    await useThumbnailStore.getState().load('p1', 'light')

    expect(items('light')).toEqual({ loaded: true, items: {} })
  })
})

describe('useThumbnailStore.needsRefresh', () => {
  it('should refresh an unknown preview', () => {
    expect(useThumbnailStore.getState().needsRefresh(TARGET)).toBe(true)
  })

  it.each([
    ['older', '2026-10-06T12:00:00', true],
    ['the same', TARGET.version, false],
    ['newer', '2026-10-06T13:00:00', false],
  ])('should refresh a preview of an %s version: %s', async (_label, version, expected) => {
    vi.mocked(listDiagramThumbnails).mockResolvedValue([listed({ version })])
    await useThumbnailStore.getState().load('p1', 'dark')

    expect(useThumbnailStore.getState().needsRefresh(TARGET)).toBe(expected)
  })
})

describe('useThumbnailStore.capture', () => {
  it('should upload both themes and show them on the cards right away', async () => {
    vi.mocked(renderDiagramThumbnails).mockResolvedValue({
      light: { base64: 'LIGHT', mimeType: 'image/webp' },
      dark: { base64: 'DARK', mimeType: 'image/png' },
    })
    vi.mocked(saveDiagramThumbnail).mockResolvedValue()

    await useThumbnailStore.getState().capture(EDITOR, TARGET)

    expect(renderDiagramThumbnails).toHaveBeenCalledWith(EDITOR)
    expect(saveDiagramThumbnail).toHaveBeenCalledWith('d1', {
      version: TARGET.version,
      light_base64: 'LIGHT',
      dark_base64: 'DARK',
    })
    expect(items('light')).toEqual({
      loaded: false,
      items: { d1: { src: 'data:image/webp;base64,LIGHT', version: TARGET.version } },
    })
    expect(items('dark').items.d1.src).toBe('data:image/png;base64,DARK')
    expect(useThumbnailStore.getState().needsRefresh(TARGET)).toBe(false)
  })

  it('should clear the preview of an empty diagram', async () => {
    vi.mocked(renderDiagramThumbnails).mockResolvedValue({ light: null, dark: null })
    vi.mocked(saveDiagramThumbnail).mockResolvedValue()

    await useThumbnailStore.getState().capture(EDITOR, TARGET)

    expect(saveDiagramThumbnail).toHaveBeenCalledWith('d1', { version: TARGET.version, light_base64: null, dark_base64: null })
    expect(items('light').items.d1).toEqual({ src: null, version: TARGET.version })
  })

  it('should keep the cards as they were when the upload fails', async () => {
    vi.mocked(renderDiagramThumbnails).mockResolvedValue({ light: null, dark: null })
    vi.mocked(saveDiagramThumbnail).mockRejectedValue(new Error('403'))

    await expect(useThumbnailStore.getState().capture(EDITOR, TARGET)).resolves.toBeUndefined()

    expect(useThumbnailStore.getState().byProject).toEqual({})
  })

  it('should upload nothing when the render fails', async () => {
    vi.mocked(renderDiagramThumbnails).mockRejectedValue(new Error('canvas disposed'))

    await useThumbnailStore.getState().capture(EDITOR, TARGET)

    expect(saveDiagramThumbnail).not.toHaveBeenCalled()
  })
})
