import { ARROW_LABEL_FONT_SIZES, FONT_SIZES, type TLShape } from 'tldraw'

import { effectiveFontSize, fontSizeOf, isGeo } from './geoStyle'

// meta.fontSize (px) overrides tldraw's size preset for the text of these shapes: geo labels
// through CustomGeoShapeUtil, plain text and arrow labels through the tldraw patch
// (getCustomFontSize). Without it each shape keeps tldraw's size for props.size.
export const MIN_FONT_SIZE = 8
export const MAX_FONT_SIZE = 200

const TEXT_TYPES = new Set(['geo', 'text', 'arrow'])

export function hasFontSize(shape: TLShape): boolean {
  return TEXT_TYPES.has(shape.type)
}

function sizeOf(shape: TLShape): keyof typeof FONT_SIZES {
  const size = (shape.props as { size?: unknown }).size
  return typeof size === 'string' && size in FONT_SIZES ? (size as keyof typeof FONT_SIZES) : 'm'
}

// The px the text is rendered at before the shape's own scale.
export function shapeFontSize(shape: TLShape): number {
  if (isGeo(shape)) {
    return effectiveFontSize(shape)
  }
  const presets = shape.type === 'arrow' ? ARROW_LABEL_FONT_SIZES : FONT_SIZES
  return fontSizeOf(shape) ?? presets[sizeOf(shape)]
}

export function clampFontSize(px: number): number {
  return Math.min(MAX_FONT_SIZE, Math.max(MIN_FONT_SIZE, Math.round(px)))
}
