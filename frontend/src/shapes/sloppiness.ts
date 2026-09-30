import type { Editor, TLShape } from 'tldraw'

// tldraw only knows a clean ("solid") and a hand-drawn ("draw") dash. The level in between is
// the "draw" dash plus meta.sloppiness = 'moderate', which the tldraw patch
// (getSloppinessOffsetScale) reads to halve the draw offset. Shapes without the meta key keep
// rendering exactly as before, so saved diagrams do not change.
export type Sloppiness = 'architect' | 'moderate' | 'artist'

const MODERATE = 'moderate'
const MODERATE_OFFSET_SCALE = 0.5
const NEXT_KEY = 'nextSloppiness'

function dashOf(shape: TLShape): string | undefined {
  const dash = (shape.props as { dash?: unknown }).dash
  return typeof dash === 'string' ? dash : undefined
}

export function hasDash(shape: TLShape): boolean {
  return dashOf(shape) !== undefined
}

// undefined when the shape is not a solid line (dashed/dotted strokes have no sloppiness).
export function sloppinessOf(shape: TLShape): Sloppiness | undefined {
  const dash = dashOf(shape)
  if (dash === 'solid') {
    return 'architect'
  }
  if (dash !== 'draw') {
    return undefined
  }
  return shape.meta.sloppiness === MODERATE ? 'moderate' : 'artist'
}

// Same factor as the tldraw patch, for the outlines we draw ourselves (rounded rectangles).
export function sloppinessOffsetScale(shape: TLShape): number {
  return shape.meta.sloppiness === MODERATE ? MODERATE_OFFSET_SCALE : 1
}

// Meta patches merge into the shape, so `null` is how the moderate level gets cleared.
export function sloppinessMetaPatch(level: Sloppiness): { sloppiness: string | null } {
  return { sloppiness: level === 'moderate' ? MODERATE : null }
}

function isModerateNext(editor: Editor): boolean {
  return editor.getInstanceState().meta[NEXT_KEY] === MODERATE
}

export function nextSloppinessOf(editor: Editor, dash: string): Sloppiness | null {
  if (dash === 'solid') {
    return 'architect'
  }
  if (dash !== 'draw') {
    return null
  }
  return isModerateNext(editor) ? 'moderate' : 'artist'
}

export function setNextSloppiness(editor: Editor, level: Sloppiness): void {
  const meta = editor.getInstanceState().meta
  editor.updateInstanceState({ meta: { ...meta, [NEXT_KEY]: level === 'moderate' ? MODERATE : null } })
}

// New hand-drawn shapes inherit the moderate level, the way tldraw applies its own styles.
// Shapes arriving from other peers are left untouched so every client renders the same thing.
export function registerSloppinessDefaults(editor: Editor): () => void {
  return editor.sideEffects.registerBeforeCreateHandler('shape', (shape, source) => {
    if (source === 'remote' || dashOf(shape) !== 'draw' || shape.meta.sloppiness !== undefined || !isModerateNext(editor)) {
      return shape
    }
    return { ...shape, meta: { ...shape.meta, sloppiness: MODERATE } }
  })
}
