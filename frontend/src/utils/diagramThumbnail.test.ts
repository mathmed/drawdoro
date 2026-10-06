import type { Editor, TLImageExportOptions } from 'tldraw'
import { describe, expect, it, vi } from 'vitest'

import { canStoreThumbnail, renderDiagramThumbnails, THUMBNAIL_MAX_BYTES, thumbnailScale } from './diagramThumbnail'

const BOUNDS = { x: 0, y: 0, w: 1000, h: 200 }

function fakeEditor(options: { ids?: string[]; sizes?: number[]; type?: string; bounds?: typeof BOUNDS }) {
  const sizes = [...(options.sizes ?? [10])]
  const toImage = vi.fn(async (_ids: string[], _opts: TLImageExportOptions) => {
    const size = sizes.length > 1 ? (sizes.shift() as number) : sizes[0]
    return { blob: new Blob([new Uint8Array(size)], { type: options.type ?? 'image/webp' }), width: 1, height: 1 }
  })
  const editor = {
    getCurrentPageShapeIds: () => new Set(options.ids ?? ['shape:a', 'shape:b']),
    getCurrentPageBounds: () => ('bounds' in options ? options.bounds : BOUNDS),
    toImage,
  } as unknown as Editor
  return { editor, toImage }
}

describe('thumbnailScale', () => {
  it('should never enlarge a small diagram', () => {
    expect(thumbnailScale(40, 20)).toBe(1)
  })

  it('should shrink a wide diagram to the preview width', () => {
    expect(thumbnailScale(3184, 100)).toBeCloseTo(0.1)
  })

  it('should shrink a tall diagram to the preview height', () => {
    expect(thumbnailScale(100, 1264)).toBeCloseTo(0.1)
  })

  it('should cope with a diagram that has no size', () => {
    expect(thumbnailScale(-50, -50)).toBe(1)
  })
})

describe('canStoreThumbnail', () => {
  it('should let anyone store previews when sign-in is off', () => {
    expect(canStoreThumbnail(null, false)).toBe(true)
  })

  it.each([
    ['owner', true],
    ['editor', true],
    ['viewer', false],
    [null, false],
  ] as const)('should let a %s store previews: %s', (role, expected) => {
    expect(canStoreThumbnail(role, true)).toBe(expected)
  })
})

describe('renderDiagramThumbnails', () => {
  it('should render nothing for an empty page', async () => {
    const { editor, toImage } = fakeEditor({ ids: [] })

    await expect(renderDiagramThumbnails(editor)).resolves.toEqual({ light: null, dark: null })
    expect(toImage).not.toHaveBeenCalled()
  })

  it('should render nothing when the page has no bounds', async () => {
    const { editor, toImage } = fakeEditor({ bounds: undefined })

    await expect(renderDiagramThumbnails(editor)).resolves.toEqual({ light: null, dark: null })
    expect(toImage).not.toHaveBeenCalled()
  })

  it('should render a transparent light and dark preview of the whole page', async () => {
    const { editor, toImage } = fakeEditor({ sizes: [3] })

    const rendered = await renderDiagramThumbnails(editor)

    expect(rendered).toEqual({
      light: { base64: 'AAAA', mimeType: 'image/webp' },
      dark: { base64: 'AAAA', mimeType: 'image/webp' },
    })
    expect(toImage).toHaveBeenCalledTimes(2)
    const [lightIds, light] = toImage.mock.calls[0]
    const [, dark] = toImage.mock.calls[1]
    expect(lightIds).toEqual(['shape:a', 'shape:b'])
    expect(light).toMatchObject({ format: 'webp', background: false, darkMode: false, pixelRatio: 2 })
    expect(light.scale).toBeCloseTo(thumbnailScale(BOUNDS.w, BOUNDS.h))
    expect(dark).toMatchObject({ darkMode: true })
  })

  it('should keep the type the browser really encoded', async () => {
    const { editor } = fakeEditor({ type: 'image/png' })

    const rendered = await renderDiagramThumbnails(editor)

    expect(rendered.light?.mimeType).toBe('image/png')
  })

  it('should call an untyped render a PNG', async () => {
    const { editor } = fakeEditor({ type: '' })

    const rendered = await renderDiagramThumbnails(editor)

    expect(rendered.dark?.mimeType).toBe('image/png')
  })

  it('should retry a render over the size limit at half the scale', async () => {
    const { editor, toImage } = fakeEditor({ sizes: [THUMBNAIL_MAX_BYTES + 1, THUMBNAIL_MAX_BYTES, 3] })

    const rendered = await renderDiagramThumbnails(editor)

    expect(rendered.light).not.toBeNull()
    expect(toImage.mock.calls[1][1].scale).toBeCloseTo(toImage.mock.calls[0][1].scale! / 2)
  })

  it('should leave out a theme that is still over the limit at half the scale', async () => {
    const { editor, toImage } = fakeEditor({ sizes: [THUMBNAIL_MAX_BYTES + 1, THUMBNAIL_MAX_BYTES + 1, 3] })

    const rendered = await renderDiagramThumbnails(editor)

    expect(rendered.light).toBeNull()
    expect(rendered.dark).not.toBeNull()
    expect(toImage).toHaveBeenCalledTimes(3)
  })
})
