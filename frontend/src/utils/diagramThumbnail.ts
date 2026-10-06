import type { Box, Editor, TLShapeId } from 'tldraw'

import type { WorkspaceRole } from '../api/types'
import { blobToBase64 } from './blob'

// The card preview is about 320 x 118 CSS pixels at its widest; rendering at twice that keeps it
// sharp on HiDPI screens. Small diagrams are never enlarged, big ones shrink to fit.
const PREVIEW_WIDTH = 320
const PREVIEW_HEIGHT = 128
const PIXEL_RATIO = 2
// Canvas units around the content, so strokes at the edges are not clipped.
const PADDING = 8
// Lossy WebP keeps previews a few kilobytes; browsers that can't encode it fall back to PNG.
const WEBP_QUALITY = 0.85
// Mirrors DIAGRAM_THUMBNAIL_MAX_BYTES in the API: a bigger render is retried at half the scale once,
// then left out.
export const THUMBNAIL_MAX_BYTES = 64 * 1024

export interface RenderedImage {
  base64: string
  mimeType: string
}

export interface RenderedThumbnails {
  // Null when there is nothing to draw or the render did not fit the size limit.
  light: RenderedImage | null
  dark: RenderedImage | null
}

export function thumbnailScale(width: number, height: number): number {
  return Math.min(
    1,
    PREVIEW_WIDTH / Math.max(width + 2 * PADDING, 1),
    PREVIEW_HEIGHT / Math.max(height + 2 * PADDING, 1),
  )
}

// Viewers never store previews, and with sign-in on nothing is sent while the role is unknown.
export function canStoreThumbnail(role: WorkspaceRole | null, authEnabled: boolean): boolean {
  if (!authEnabled) {
    return true
  }
  return role === 'owner' || role === 'editor'
}

async function renderTheme(
  editor: Editor,
  ids: TLShapeId[],
  bounds: Box,
  darkMode: boolean,
): Promise<RenderedImage | null> {
  let scale = thumbnailScale(bounds.w, bounds.h)
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const { blob } = await editor.toImage(ids, {
      format: 'webp',
      quality: WEBP_QUALITY,
      // Transparent, so the card's own (themed) background shows through.
      background: false,
      darkMode,
      scale,
      pixelRatio: PIXEL_RATIO,
      padding: PADDING,
    })
    if (blob.size <= THUMBNAIL_MAX_BYTES) {
      // The blob says what the browser really encoded: WebP, or PNG where WebP is not supported.
      return { base64: await blobToBase64(blob), mimeType: blob.type === '' ? 'image/png' : blob.type }
    }
    scale /= 2
  }
  return null
}

// One render per theme, one after the other so a big diagram never renders twice at once.
export async function renderDiagramThumbnails(editor: Editor): Promise<RenderedThumbnails> {
  const ids = [...editor.getCurrentPageShapeIds()]
  const bounds = editor.getCurrentPageBounds()
  if (ids.length === 0 || bounds === undefined) {
    return { light: null, dark: null }
  }
  const light = await renderTheme(editor, ids, bounds, false)
  const dark = await renderTheme(editor, ids, bounds, true)
  return { light, dark }
}
