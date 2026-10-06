import { cloneElement, isValidElement, type CSSProperties, type ReactElement, type ReactNode } from 'react'
import {
  FONT_FAMILIES,
  GeoShapeUtil,
  renderHtmlFromRichTextForMeasurement,
  SVGContainer,
  TEXT_PROPS,
  type Editor,
  type Geometry2d,
  type Group2d,
  type SvgExportContext,
  type TLGeoShape,
} from 'tldraw'

import { CustomFill, RoundedBody } from './GeoPaint'
import {
  effectiveFontSize,
  fontSizeOf,
  followsStroke,
  hexOrUndefined,
  isGeo,
  isRounded,
  radiusFor,
  safeId,
  strokeColorOf,
  type Edges,
} from './geoStyle'

// Mirrors tldraw's (unexported) label padding so our measurements match its layout.
const LABEL_PADDING = 16

function isEmptyText(shape: TLGeoShape): boolean {
  const content = shape.props.richText.content as { content?: unknown[] }[]
  return content.length === 0 || (content.length === 1 && (content[0].content ?? []).length === 0)
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

export class CustomGeoShapeUtil extends GeoShapeUtil {
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

const NEXT_KEY = 'nextGeoDefaults'

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

// New geo shapes inherit the last edges/colour choices, the way tldraw applies its own styles;
// text and arrows inherit the font size. Shapes arriving from other peers are left untouched so
// every client renders the same thing.
export function registerGeoDefaults(editor: Editor): () => void {
  return editor.sideEffects.registerBeforeCreateHandler('shape', (shape, source) => {
    if (source === 'remote') {
      return shape
    }
    const next = getNextDefaults(editor)
    if (!isGeo(shape)) {
      const takesFontSize = shape.type === 'text' || shape.type === 'arrow'
      if (!takesFontSize || shape.meta.fontSize !== undefined || next.fontSize === null) {
        return shape
      }
      return { ...shape, meta: { ...shape.meta, fontSize: next.fontSize } }
    }
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
