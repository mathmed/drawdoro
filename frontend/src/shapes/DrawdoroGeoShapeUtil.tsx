import { cloneElement, isValidElement, type CSSProperties, type ReactElement, type ReactNode } from 'react'
import {
  FONT_FAMILIES,
  GeoShapeUtil,
  LABEL_FONT_SIZES,
  PathBuilder,
  renderHtmlFromRichTextForMeasurement,
  STROKE_SIZES,
  SVGContainer,
  TEXT_PROPS,
  useDefaultColorTheme,
  type Editor,
  type TLDefaultColorTheme,
  type Geometry2d,
  type Group2d,
  type SvgExportContext,
  type TLGeoShape,
  type TLShape,
} from 'tldraw'

// Excalidraw-style extras that tldraw does not model. They live in `meta`, so they are saved,
// synced and exported with the shape while plain tldraw keeps rendering its defaults.
//   meta.edges       'sharp' | 'round'   rounded corners (rectangles only)
//   meta.strokeColor '#rrggbb'           custom colour, overrides props.color; fills derive their
//                                        tint from it exactly like tldraw does for its palette
//   meta.fontSize    number (px)         label size independent from the stroke width

export type Edges = 'sharp' | 'round'

const MAX_RADIUS = 32
// Mirrors tldraw's (unexported) label padding so our measurements match its layout.
const LABEL_PADDING = 16

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

function hexOrUndefined(value: unknown): string | undefined {
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

function isEmptyText(shape: TLGeoShape): boolean {
  const content = shape.props.richText.content as { content?: unknown[] }[]
  return content.length === 0 || (content.length === 1 && (content[0].content ?? []).length === 0)
}

function mix(hex: string, target: string, amount: number): string {
  const channel = (value: string, index: number) => parseInt(value.slice(1 + index * 2, 3 + index * 2), 16)
  const parts = [0, 1, 2].map((index) => Math.round(channel(hex, index) + (channel(target, index) - channel(hex, index)) * amount))
  return `#${parts.map((part) => part.toString(16).padStart(2, '0')).join('')}`
}

interface DerivedFill {
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

function derivedFill(hex: string, theme: TLDefaultColorTheme): DerivedFill {
  return fillTintsFor(hex, theme.id === 'dark')
}

// Only fills that take their colour from the stroke need to follow a custom stroke.
function followsStroke(shape: TLGeoShape): boolean {
  return strokeColorOf(shape) !== undefined && ['solid', 'fill', 'pattern'].includes(shape.props.fill)
}

function isRounded(shape: TLGeoShape): boolean {
  return shape.props.geo === 'rectangle' && edgesOf(shape) === 'round'
}

// Same proportions as Excalidraw's "round" edges: a quarter of the short side, capped.
function radiusFor(w: number, h: number, scale: number): number {
  return Math.min(Math.min(w, h) / 4, MAX_RADIUS * scale)
}

function safeId(value: string): string {
  return value.replace(/[^a-zA-Z0-9]/g, '')
}

function Hatch({ id, color, scale }: { id: string; color: string; scale: number }) {
  return (
    <defs>
      <pattern id={id} width={8 * scale} height={8 * scale} patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
        <line x1="0" y1="0" x2="0" y2={8 * scale} stroke={color} strokeWidth={2 * scale} />
      </pattern>
    </defs>
  )
}

// Fill drawn under tldraw's outline when a custom stroke colour drives the tint.
function CustomFill({ shape, d, scale }: { shape: TLGeoShape; d: string; scale: number }) {
  const theme = useDefaultColorTheme()
  const stroke = strokeColorOf(shape)
  if (stroke === undefined || !followsStroke(shape)) {
    return null
  }
  const colors = derivedFill(stroke, theme)
  if (shape.props.fill !== 'pattern') {
    return <path d={d} fill={shape.props.fill === 'fill' ? colors.solid : colors.tint} />
  }
  const id = `dd-fill-${safeId(shape.id)}`
  return (
    <>
      <path d={d} fill={colors.tint} />
      <Hatch id={id} color={colors.hatch} scale={scale} />
      <path d={d} fill={`url(#${id})`} />
    </>
  )
}

function RoundedBody({ shape, w, h, scale }: { shape: TLGeoShape; w: number; h: number; scale: number }) {
  const theme = useDefaultColorTheme()
  const { color, fill, dash, size } = shape.props
  const strokeWidth = STROKE_SIZES[size] * scale
  const roundness = radiusFor(w, h, scale)
  const path = new PathBuilder().moveTo(0, 0, { geometry: { isFilled: fill !== 'none' } }).lineTo(w, 0).lineTo(w, h).lineTo(0, h).close()
  const clean = { strokeWidth, randomSeed: shape.id, passes: 1, offset: 0, roundness }
  const fillD = path.toDrawD({ ...clean, onlyFilled: true })
  const stroke = strokeColorOf(shape) ?? theme[color].solid
  const patternId = `dd-hatch-${safeId(shape.id)}`

  let fillNode: ReactNode = null
  if (followsStroke(shape)) {
    fillNode = <CustomFill shape={shape} d={fillD} scale={scale} />
  } else if (fill !== 'none') {
    const fillColor = {
      semi: theme.solid,
      solid: theme[color].semi,
      fill: theme[color].fill,
      pattern: `url(#${patternId})`,
    }[fill]
    fillNode = (
      <>
        {fill === 'pattern' ? (
          <>
            <path d={fillD} fill={theme[color].semi} />
            <Hatch id={patternId} color={theme[color].pattern} scale={scale} />
          </>
        ) : null}
        <path d={fillD} fill={fillColor} />
      </>
    )
  }

  let outline: ReactNode
  if (dash === 'draw') {
    outline = path.toSvg({ style: 'draw', strokeWidth, randomSeed: shape.id, roundness, props: { fill: 'none', stroke } })
  } else {
    const dashArray = { solid: undefined, dashed: `${strokeWidth * 2} ${strokeWidth * 2}`, dotted: `0 ${strokeWidth * 2}` }[dash]
    outline = (
      <path
        d={path.toDrawD(clean)}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeDasharray={dashArray}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    )
  }

  return (
    <>
      {fillNode}
      {outline}
    </>
  )
}

function withoutFill(shape: TLGeoShape): TLGeoShape {
  return { ...shape, props: { ...shape.props, fill: 'none' } }
}

// Same growth rule as tldraw's geo shape, measured at our own font size: the shape grows
// (growY) until the label fits, and shrinks back when it no longer needs to.
function fitLabel(editor: Editor, shape: TLGeoShape, fontPx: number): TLGeoShape {
  const { scale, w, h, font, richText } = shape.props
  if (isEmptyText(shape)) {
    return shape.props.growY === 0 ? shape : { ...shape, props: { ...shape.props, growY: 0 } }
  }
  const html = renderHtmlFromRichTextForMeasurement(editor, richText)
  const text = editor.textMeasure.measureHtml(html, {
    ...TEXT_PROPS,
    fontFamily: FONT_FAMILIES[font],
    fontSize: fontPx,
    maxWidth: Math.max(0, Math.ceil(w / scale - LABEL_PADDING * 2)),
  })
  const labelW = text.w + LABEL_PADDING * 2
  const labelH = text.h + LABEL_PADDING * 2
  const unscaledH = h / scale
  const growY = labelH > unscaledH ? labelH - unscaledH : 0
  return {
    ...shape,
    props: { ...shape.props, growY: growY * scale, w: Math.max(w / scale, labelW) * scale },
  }
}

export class DrawdoroGeoShapeUtil extends GeoShapeUtil {
  override onBeforeCreate(shape: TLGeoShape) {
    const base = super.onBeforeCreate(shape) ?? shape
    const fontPx = fontSizeOf(base)
    return fontPx === undefined ? (base === shape ? undefined : base) : fitLabel(this.editor, base, fontPx)
  }

  override onBeforeUpdate(prev: TLGeoShape, next: TLGeoShape) {
    const base = super.onBeforeUpdate(prev, next) ?? next
    const fontPx = fontSizeOf(next)
    const fontSizeChanged = fontPx !== fontSizeOf(prev)
    const layoutChanged =
      prev.props.richText !== next.props.richText ||
      prev.props.font !== next.props.font ||
      prev.props.size !== next.props.size ||
      prev.props.w !== next.props.w
    // tldraw measures at its own size; redo it whenever the custom size is involved,
    // including when it is removed (so the shape shrinks back to tldraw's size).
    if (fontSizeChanged || (fontPx !== undefined && layoutChanged)) {
      return fitLabel(this.editor, base, effectiveFontSize(next))
    }
    return base === next ? undefined : base
  }

  private outlinePath(shape: TLGeoShape): string {
    const outline = (this.getGeometry(shape) as Group2d).children[0] as Geometry2d
    return outline.getSvgPathData(true)
  }

  override component(shape: TLGeoShape) {
    const strokeColor = strokeColorOf(shape)
    const customFill = followsStroke(shape)
    const rounded = isRounded(shape)
    // tldraw would paint the tint of props.color, so it renders without fill and we paint the
    // tint of the custom colour instead. The base renderer always runs because it uses hooks:
    // skipping it would change the hook order when a shape changes.
    const base = super.component(customFill ? withoutFill(shape) : shape)

    const fontPx = fontSizeOf(shape)
    const { w, h, growY, scale } = shape.props
    // tldraw sets the label size inline; the CSS variable overrides it for display and editing.
    const withFont = (node: ReactElement): ReactElement =>
      fontPx === undefined ? (
        node
      ) : (
        <div className="dd-font" style={{ '--dd-font-size': `${fontPx * scale}px` } as CSSProperties}>
          {node}
        </div>
      )

    if (!rounded && strokeColor === undefined) {
      return withFont(base)
    }

    if (rounded) {
      return withFont(
        <>
          <SVGContainer>
            <RoundedBody shape={shape} w={Math.max(1, w)} h={Math.max(1, h + growY)} scale={scale} />
          </SVGContainer>
          <div className="dd-rounded-geo">{base}</div>
        </>,
      )
    }

    return withFont(
      <>
        {customFill ? (
          <SVGContainer>
            <CustomFill shape={shape} d={this.outlinePath(shape)} scale={scale} />
          </SVGContainer>
        ) : null}
        <div
          className={strokeColor !== undefined ? 'dd-custom-stroke' : 'dd-geo'}
          style={{ '--dd-stroke': strokeColor } as CSSProperties}
        >
          {base}
        </div>
      </>,
    )
  }

  override indicator(shape: TLGeoShape) {
    const base = super.indicator(shape)
    if (!isRounded(shape)) {
      return base
    }
    const { w, h, growY, scale } = shape.props
    const height = Math.max(1, h + growY)
    const radius = radiusFor(w, height, scale)
    return <rect width={Math.max(1, w)} height={height} rx={radius} ry={radius} />
  }

  override toSvg(shape: TLGeoShape, ctx: SvgExportContext) {
    const strokeColor = strokeColorOf(shape)
    const customFill = followsStroke(shape)
    const rounded = isRounded(shape)
    const fontPx = fontSizeOf(shape)
    if (!rounded && strokeColor === undefined && fontPx === undefined) {
      return super.toSvg(shape, ctx)
    }
    const base = super.toSvg(customFill ? withoutFill(shape) : shape, ctx)
    if (!isValidElement(base)) {
      return base
    }
    // The base export is <><Body /><Label /></>: the body gets our edges/colours, the label our size.
    const children = (base as ReactElement<{ children: ReactNode[] }>).props.children
    const [body, rawLabel] = Array.isArray(children) ? children : [base, null]
    const label =
      fontPx !== undefined && isValidElement(rawLabel)
        ? cloneElement(rawLabel as ReactElement<{ fontSize: number }>, { fontSize: fontPx })
        : rawLabel
    const { scale } = shape.props
    const w = shape.props.w / scale
    const h = (shape.props.h + shape.props.growY) / scale

    if (rounded) {
      return (
        <>
          <RoundedBody shape={shape} w={w} h={h} scale={1} />
          {label}
        </>
      )
    }

    // Exported SVGs carry no app CSS, so the stroke override ships as an inline <style>.
    let strokeClass: string | undefined
    if (strokeColor !== undefined) {
      strokeClass = `dd-stroke-${safeId(strokeColor)}`
      const selector = `.${strokeClass} [stroke]:not([stroke="none"])`
      ctx.addExportDef({
        key: strokeClass,
        getElement: () => <style>{`${selector}{stroke:${strokeColor}}`}</style>,
      })
    }
    const unscaled = { ...shape, props: { ...shape.props, w, h, growY: 0, scale: 1 } }
    return (
      <>
        {customFill ? <CustomFill shape={shape} d={this.outlinePath(unscaled)} scale={1} /> : null}
        <g className={strokeClass}>{body}</g>
        {label}
      </>
    )
  }
}

interface NextShapeDefaults {
  edges: Edges
  strokeColor: string | null
  fontSize: number | null
}

const NEXT_KEY = 'drawdoroNextGeo'

export function getNextDefaults(editor: Editor): NextShapeDefaults {
  const stored = editor.getInstanceState().meta[NEXT_KEY] as Partial<NextShapeDefaults> | undefined
  return {
    edges: stored?.edges === 'round' ? 'round' : 'sharp',
    strokeColor: hexOrUndefined(stored?.strokeColor) ?? null,
    fontSize: typeof stored?.fontSize === 'number' ? stored.fontSize : null,
  }
}

export function setNextDefaults(editor: Editor, patch: Partial<NextShapeDefaults>): void {
  const meta = editor.getInstanceState().meta
  editor.updateInstanceState({ meta: { ...meta, [NEXT_KEY]: { ...getNextDefaults(editor), ...patch } } })
}

// New geo shapes inherit the last edges/colour choices, the way tldraw applies its own styles.
// Shapes arriving from other peers are left untouched so every client renders the same thing.
export function registerGeoDefaults(editor: Editor): () => void {
  return editor.sideEffects.registerBeforeCreateHandler('shape', (shape, source) => {
    if (source === 'remote' || !isGeo(shape)) {
      return shape
    }
    const next = getNextDefaults(editor)
    const meta = { ...shape.meta }
    if (meta.edges === undefined && shape.props.geo === 'rectangle') {
      meta.edges = next.edges
    }
    if (meta.strokeColor === undefined && next.strokeColor !== null) {
      meta.strokeColor = next.strokeColor
    }
    if (meta.fontSize === undefined && next.fontSize !== null) {
      meta.fontSize = next.fontSize
    }
    return { ...shape, meta }
  })
}
