import { LABEL_FONT_SIZES, type TLGeoShape, type TLShape } from 'tldraw'

// Excalidraw-style extras that tldraw does not model. They live in `meta`, so they are saved,
// synced and exported with the shape while plain tldraw keeps rendering its defaults.
//   meta.edges       'sharp' | 'round'   rounded corners (rectangles only)
//   meta.strokeColor '#rrggbb'           custom colour, overrides props.color; fills derive their
//                                        tint from it exactly like tldraw does for its palette
//   meta.fontSize    number (px)         label size independent from the stroke width (also read
//                                        by the tldraw patch for text and arrow labels)

export type Edges = 'sharp' | 'round'

const MAX_RADIUS = 32

// Excalidraw-like font sizes (M matches tldraw's default label size, so it shows as active
// on untouched shapes); tldraw alone only offers 18–32px and ties them to the stroke width.
export const FONT_SIZE_PRESETS = [
  { label: 'S', px: 16 },
  { label: 'M', px: 22 },
  { label: 'L', px: 28 },
  { label: 'XL', px: 36 },
]

export function isGeo(shape: TLShape): shape is TLGeoShape {
  return shape.type === 'geo'
}

export function isRoundable(shape: TLShape): shape is TLGeoShape {
  return isGeo(shape) && shape.props.geo === 'rectangle'
}

export function edgesOf(shape: TLShape): Edges {
  return shape.meta.edges === 'round' ? 'round' : 'sharp'
}

export function hexOrUndefined(value: unknown): string | undefined {
  return typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value) ? value : undefined
}

export function strokeColorOf(shape: TLShape): string | undefined {
  return hexOrUndefined(shape.meta.strokeColor)
}

export function fontSizeOf(shape: TLShape): number | undefined {
  const value = shape.meta.fontSize
  return typeof value === 'number' && value > 0 ? value : undefined
}

// The px the label is actually rendered at: the custom size, or tldraw's size for props.size.
export function effectiveFontSize(shape: TLGeoShape): number {
  return fontSizeOf(shape) ?? LABEL_FONT_SIZES[shape.props.size]
}

function mix(hex: string, target: string, amount: number): string {
  const channel = (value: string, index: number) => parseInt(value.slice(1 + index * 2, 3 + index * 2), 16)
  const parts = [0, 1, 2].map((index) => Math.round(channel(hex, index) + (channel(target, index) - channel(hex, index)) * amount))
  return `#${parts.map((part) => part.toString(16).padStart(2, '0')).join('')}`
}

export interface DerivedFill {
  tint: string
  solid: string
  hatch: string
}

// Mirrors how tldraw builds its palette: the tint is the colour ~80% of the way to the canvas
// background and the hatch lines stay close to the colour itself.
export function fillTintsFor(hex: string, isDarkMode: boolean): DerivedFill {
  const background = isDarkMode ? '#101011' : '#f9fafb'
  return { tint: mix(hex, background, isDarkMode ? 0.72 : 0.82), solid: hex, hatch: mix(hex, background, 0.18) }
}

// Only fills that take their colour from the stroke need to follow a custom stroke.
export function followsStroke(shape: TLGeoShape): boolean {
  return strokeColorOf(shape) !== undefined && ['solid', 'fill', 'pattern'].includes(shape.props.fill)
}

export function isRounded(shape: TLGeoShape): boolean {
  return shape.props.geo === 'rectangle' && edgesOf(shape) === 'round'
}

// Same proportions as Excalidraw's "round" edges: a quarter of the short side, capped.
export function radiusFor(w: number, h: number, scale: number): number {
  return Math.min(Math.min(w, h) / 4, MAX_RADIUS * scale)
}

export function safeId(value: string): string {
  return value.replace(/[^a-zA-Z0-9]/g, '')
}
