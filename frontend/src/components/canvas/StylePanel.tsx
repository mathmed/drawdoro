import {
  Circle,
  Cloud,
  Diamond,
  Hexagon,
  Square,
  Triangle,
  type LucideIcon,
} from 'lucide-react'
import type { ReactNode } from 'react'

import {
  effectiveFontSize,
  FONT_SIZE_PRESETS,
  edgesOf,
  fillTintsFor,
  getNextDefaults,
  isGeo,
  isRoundable,
  setNextDefaults,
  strokeColorOf,
  type Edges,
} from '../../shapes/DrawdoroGeoShapeUtil'
import {
  ArrowShapeArrowheadEndStyle,
  ArrowShapeArrowheadStartStyle,
  ArrowShapeKindStyle,
  DefaultColorStyle,
  DefaultDashStyle,
  DefaultFillStyle,
  DefaultFontStyle,
  DefaultMenuPanel,
  DefaultSizeStyle,
  DefaultStylePanel,
  DefaultTextAlignStyle,
  GeoShapeGeoStyle,
  getDefaultColorTheme,
  PORTRAIT_BREAKPOINT,
  useBreakpoint,
  useEditor,
  useReadonly,
  useRelevantStyles,
  useValue,
  type ReadonlySharedStyleMap,
  type StyleProp,
  type TLUiStylePanelProps,
} from 'tldraw'

type Color = (typeof DefaultColorStyle)['defaultValue']

const COLORS: Color[] = [
  'black',
  'grey',
  'light-violet',
  'violet',
  'blue',
  'light-blue',
  'yellow',
  'orange',
  'green',
  'light-green',
  'light-red',
  'red',
  'white',
]

const OPACITIES = [0.1, 0.25, 0.5, 0.75, 1]

const GEOS: { value: (typeof GeoShapeGeoStyle)['defaultValue']; icon: LucideIcon; label: string }[] = [
  { value: 'rectangle', icon: Square, label: 'Rectangle' },
  { value: 'ellipse', icon: Circle, label: 'Ellipse' },
  { value: 'diamond', icon: Diamond, label: 'Diamond' },
  { value: 'triangle', icon: Triangle, label: 'Triangle' },
  { value: 'hexagon', icon: Hexagon, label: 'Hexagon' },
  { value: 'cloud', icon: Cloud, label: 'Cloud' },
]

type Arrowhead = (typeof ArrowShapeArrowheadEndStyle)['defaultValue']

const ARROWHEADS: Arrowhead[] = ['none', 'arrow', 'triangle', 'dot', 'diamond']

function sharedValue<T>(styles: ReadonlySharedStyleMap, style: StyleProp<T>): T | null | undefined {
  const shared = styles.get(style)
  if (shared === undefined) {
    return undefined
  }
  return shared.type === 'shared' ? shared.value : null
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="sp-section">
      <div className="sp-title">{title}</div>
      <div className="sp-row">{children}</div>
    </div>
  )
}

function Option({
  active,
  label,
  onSelect,
  disabled = false,
  children,
}: {
  active: boolean
  label: string
  onSelect: () => void
  disabled?: boolean
  children: ReactNode
}) {
  return (
    <button
      type="button"
      className="sp-option"
      aria-pressed={active}
      title={label}
      aria-label={label}
      disabled={disabled}
      onClick={onSelect}
    >
      {children}
    </button>
  )
}

function ColorPick({
  value,
  active,
  label,
  onOpen,
  onPick,
}: {
  value: string | undefined
  active: boolean
  label: string
  onOpen: () => void
  onPick: (hex: string) => void
}) {
  return (
    <label
      className="sp-swatch sp-pick"
      data-active={active}
      data-empty={value === undefined}
      title={label}
      style={value !== undefined ? { background: value } : undefined}
    >
      <input
        type="color"
        aria-label={label}
        value={value ?? '#1e1e1e'}
        onClick={onOpen}
        onChange={(event) => onPick(event.target.value)}
      />
    </label>
  )
}

function Line({ width, dash }: { width: number; dash?: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden>
      <line x1="3" y1="9" x2="15" y2="9" stroke="currentColor" strokeWidth={width} strokeDasharray={dash} strokeLinecap="round" />
    </svg>
  )
}

function Squiggle({ wobble }: { wobble: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
      {wobble ? <path d="M2 11c2-4 3-4 5-1s3 3 5-1 3-3 4 0" /> : <path d="M2 12c3-5 6-5 7-2s4 3 7-3" />}
    </svg>
  )
}

function ArrowheadIcon({ head, flip }: { head: Arrowhead; flip: boolean }) {
  const tip: Record<Arrowhead, ReactNode> = {
    none: null,
    arrow: <path d="M11 5l4 4-4 4" fill="none" />,
    triangle: <path d="M11 5l4 4-4 4z" fill="currentColor" />,
    dot: <circle cx="13.5" cy="9" r="2.3" fill="currentColor" />,
    diamond: <path d="M13 6l3 3-3 3-3-3z" fill="currentColor" />,
    bar: <path d="M15 5v8" />,
    inverted: <path d="M15 5l-4 4 4 4z" fill="currentColor" />,
    pipe: <path d="M15 5v8" />,
    square: <rect x="11" y="7" width="4" height="4" fill="currentColor" />,
  }
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      aria-hidden
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={flip ? { transform: 'scaleX(-1)' } : undefined}
    >
      <line x1="3" y1="9" x2={head === 'none' ? 15 : 13} y2="9" />
      {tip[head]}
    </svg>
  )
}

function DrawdoroStylePanelContent() {
  const editor = useEditor()
  const styles = useRelevantStyles()
  const isDarkMode = useValue('dark mode', () => editor.user.getIsDarkMode(), [editor])
  const opacity = useValue('opacity', () => editor.getSharedOpacity(), [editor])
  // undefined: not applicable · null: mixed selection
  const edges = useValue<Edges | null | undefined>(
    'edges',
    () => {
      const selected = editor.getSelectedShapes()
      if (editor.isIn('select') && selected.length > 0) {
        if (!selected.every(isRoundable)) {
          return undefined
        }
        const values = new Set(selected.map(edgesOf))
        return values.size === 1 ? [...values][0] : null
      }
      return editor.isIn('geo') ? getNextDefaults(editor).edges : undefined
    },
    [editor],
  )
  // Custom stroke colours are a Drawdoro extension of geo shapes: '' means "use tldraw's palette",
  // null means the selection disagrees, undefined means the selection is not all geo shapes.
  const geoColors = useValue(
    'geo colors',
    () => {
      const selected = editor.getSelectedShapes()
      if (!editor.isIn('select') || selected.length === 0 || !selected.every(isGeo)) {
        return undefined
      }
      const shared = (values: string[]): string | null => (new Set(values).size === 1 ? values[0] : null)
      return { stroke: shared(selected.map((shape) => strokeColorOf(shape) ?? '')) }
    },
    [editor],
  )
  // Label size of geo shapes, independent from the stroke width (null when they disagree).
  const geoFontSize = useValue(
    'geo font size',
    () => {
      const selected = editor.getSelectedShapes()
      if (!editor.isIn('select') || selected.length === 0 || !selected.every(isGeo)) {
        return undefined
      }
      const sizes = new Set(selected.map((shape) => effectiveFontSize(shape)))
      return sizes.size === 1 ? [...sizes][0] : null
    },
    [editor],
  )
  // For plain text, tldraw's size only drives the font, so that section is labelled as such.
  const isTextOnly = useValue(
    'text only',
    () => {
      const selected = editor.getSelectedShapes()
      return selected.length > 0 && selected.every((shape) => shape.type === 'text')
    },
    [editor],
  )
  // tldraw always renders arrows with a clean stroke, so sloppiness would be a no-op for them.
  const sloppinessApplies = useValue(
    'sloppiness applies',
    () => {
      const selected = editor.getSelectedShapes()
      if (editor.isIn('select') && selected.length > 0) {
        return selected.some((shape) => shape.type !== 'arrow')
      }
      return !editor.isIn('arrow')
    },
    [editor],
  )

  if (styles === null) {
    return null
  }

  const theme = getDefaultColorTheme({ isDarkMode })
  const color = sharedValue(styles, DefaultColorStyle)
  const fill = sharedValue(styles, DefaultFillStyle)
  const dash = sharedValue(styles, DefaultDashStyle)
  const size = sharedValue(styles, DefaultSizeStyle)
  const font = sharedValue(styles, DefaultFontStyle)
  const align = sharedValue(styles, DefaultTextAlignStyle)
  const geo = sharedValue(styles, GeoShapeGeoStyle)
  const arrowKind = sharedValue(styles, ArrowShapeKindStyle)
  const headStart = sharedValue(styles, ArrowShapeArrowheadStartStyle)
  const headEnd = sharedValue(styles, ArrowShapeArrowheadEndStyle)
  const customStroke = geoColors?.stroke ? geoColors.stroke : undefined
  const swatch =
    customStroke === undefined
      ? theme[color ?? 'black']
      : (() => {
          const tints = fillTintsFor(customStroke, isDarkMode)
          return { semi: tints.tint, fill: tints.solid, pattern: tints.hatch }
        })()

  function apply<T>(style: StyleProp<T>, value: T): void {
    editor.markHistoryStoppingPoint('change style')
    editor.run(() => {
      if (editor.isIn('select')) {
        editor.setStyleForSelectedShapes(style, value)
      }
      editor.setStyleForNextShapes(style, value)
      editor.updateInstanceState({ isChangingStyle: true })
    })
  }

  function applyEdges(value: Edges): void {
    editor.markHistoryStoppingPoint('change edges')
    editor.run(() => {
      const targets = editor.isIn('select') ? editor.getSelectedShapes().filter(isRoundable) : []
      editor.updateShapes(targets.map((shape) => ({ id: shape.id, type: shape.type, meta: { ...shape.meta, edges: value } })))
      setNextDefaults(editor, { edges: value })
    })
  }

  // Meta patches merge into the shape, so `null` is how a custom colour gets cleared.
  function updateGeoMeta(patch: Record<string, string | number | null>): void {
    const targets = editor.getSelectedShapes().filter(isGeo)
    editor.updateShapes(targets.map((shape) => ({ id: shape.id, type: shape.type, meta: { ...shape.meta, ...patch } })))
  }

  function applyStrokePalette(item: Color): void {
    apply(DefaultColorStyle, item)
    editor.run(() => {
      updateGeoMeta({ strokeColor: null })
      setNextDefaults(editor, { strokeColor: null })
    })
  }

  function applyCustomStroke(hex: string): void {
    editor.run(() => {
      updateGeoMeta({ strokeColor: hex })
      setNextDefaults(editor, { strokeColor: hex })
    })
  }

  function applyFontSize(px: number): void {
    editor.markHistoryStoppingPoint('change font size')
    editor.run(() => {
      updateGeoMeta({ fontSize: px })
      setNextDefaults(editor, { fontSize: px })
    })
  }

  function applyOpacity(value: number): void {
    editor.markHistoryStoppingPoint('change opacity')
    editor.run(() => {
      if (editor.isIn('select')) {
        editor.setOpacityForSelectedShapes(value)
      }
      editor.setOpacityForNextShapes(value)
    })
  }

  // tldraw models "sloppy" as a dash style, so stroke style and sloppiness share one prop:
  // a solid line is either `solid` (architect) or `draw` (artist).
  const isSolidLine = dash === 'solid' || dash === 'draw'

  return (
    <div className="sp">
      {color !== undefined ? (
        <Section title="Stroke">
          <div className="sp-swatches">
            {COLORS.map((item) => (
              <button
                key={item}
                type="button"
                className="sp-swatch"
                aria-pressed={color === item && (geoColors === undefined || geoColors.stroke === '')}
                title={item.replace('-', ' ')}
                aria-label={item.replace('-', ' ')}
                style={{ background: theme[item].solid }}
                onClick={() => applyStrokePalette(item)}
              />
            ))}
            {geoColors !== undefined ? (
              <ColorPick
                label="Custom stroke color"
                value={geoColors.stroke === '' || geoColors.stroke === null ? undefined : geoColors.stroke}
                active={geoColors.stroke !== '' && geoColors.stroke !== null}
                onOpen={() => editor.markHistoryStoppingPoint('pick stroke color')}
                onPick={applyCustomStroke}
              />
            ) : null}
          </div>
        </Section>
      ) : null}

      {fill !== undefined ? (
        <Section title="Fill">
          <Option active={fill === 'none'} label="Transparent" onSelect={() => apply(DefaultFillStyle, 'none')}>
            <span className="sp-fill sp-fill-none" />
          </Option>
          <Option active={fill === 'semi'} label="Canvas color" onSelect={() => apply(DefaultFillStyle, 'semi')}>
            <span className="sp-fill" style={{ background: theme.solid }} />
          </Option>
          <Option active={fill === 'solid'} label="Tint" onSelect={() => apply(DefaultFillStyle, 'solid')}>
            <span className="sp-fill" style={{ background: swatch.semi }} />
          </Option>
          <Option active={fill === 'fill'} label="Solid" onSelect={() => apply(DefaultFillStyle, 'fill')}>
            <span className="sp-fill" style={{ background: swatch.fill }} />
          </Option>
          <Option active={fill === 'pattern'} label="Hachure" onSelect={() => apply(DefaultFillStyle, 'pattern')}>
            <span
              className="sp-fill"
              style={{
                background: `repeating-linear-gradient(-45deg, ${swatch.pattern} 0 1.5px, transparent 1.5px 4px)`,
              }}
            />
          </Option>
        </Section>
      ) : null}

      {size !== undefined ? (
        <Section title={isTextOnly ? 'Font size' : 'Stroke width'}>
          {(
            [
              ['s', 'Thin', 1.25],
              ['m', 'Regular', 2.25],
              ['l', 'Bold', 3.5],
              ['xl', 'Extra bold', 5],
            ] as const
          ).map(([value, label, width], index) => (
            <Option
              key={value}
              active={size === value}
              label={isTextOnly ? value.toUpperCase() : label}
              onSelect={() => apply(DefaultSizeStyle, value)}
            >
              {/* Plain text has no stroke: tldraw's size is only its font size there. */}
              {isTextOnly ? (
                <span style={{ fontSize: 11 + index * 1.5, fontWeight: 600 }}>{value.toUpperCase()}</span>
              ) : (
                <Line width={width} />
              )}
            </Option>
          ))}
        </Section>
      ) : null}

      {geoFontSize !== undefined ? (
        <Section title="Font size">
          {FONT_SIZE_PRESETS.map(({ label, px }) => (
            <Option key={px} active={geoFontSize === px} label={`${label} — ${px}px`} onSelect={() => applyFontSize(px)}>
              <span style={{ fontSize: 11 + FONT_SIZE_PRESETS.findIndex((item) => item.px === px) * 1.5, fontWeight: 600 }}>
                {label}
              </span>
            </Option>
          ))}
        </Section>
      ) : null}

      {dash !== undefined ? (
        <>
          <Section title="Stroke style">
            <Option
              active={isSolidLine}
              label="Solid"
              onSelect={() => apply(DefaultDashStyle, dash === 'draw' ? 'draw' : 'solid')}
            >
              <Line width={2} />
            </Option>
            <Option active={dash === 'dashed'} label="Dashed" onSelect={() => apply(DefaultDashStyle, 'dashed')}>
              <Line width={2} dash="4 3" />
            </Option>
            <Option active={dash === 'dotted'} label="Dotted" onSelect={() => apply(DefaultDashStyle, 'dotted')}>
              <Line width={2} dash="0.5 3.5" />
            </Option>
          </Section>
          {sloppinessApplies ? (
          <Section title="Sloppiness">
            <Option active={dash === 'solid'} disabled={!isSolidLine} label="Architect — clean lines" onSelect={() => apply(DefaultDashStyle, 'solid')}>
              <Squiggle wobble={false} />
            </Option>
            <Option active={dash === 'draw'} disabled={!isSolidLine} label="Artist — hand-drawn" onSelect={() => apply(DefaultDashStyle, 'draw')}>
              <Squiggle wobble />
            </Option>
          </Section>
          ) : null}
        </>
      ) : null}

      {edges !== undefined ? (
        <Section title="Edges">
          <Option active={edges === 'sharp'} label="Sharp" onSelect={() => applyEdges('sharp')}>
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.6" strokeDasharray="2 2">
              <path d="M4 15V4h11" strokeDasharray="none" />
            </svg>
          </Option>
          <Option active={edges === 'round'} label="Round" onSelect={() => applyEdges('round')}>
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
              <path d="M4 15V9a5 5 0 0 1 5-5h6" />
            </svg>
          </Option>
        </Section>
      ) : null}

      {geo !== undefined ? (
        <Section title="Shape">
          {GEOS.map(({ value, icon: Icon, label }) => (
            <Option key={value} active={geo === value} label={label} onSelect={() => apply(GeoShapeGeoStyle, value)}>
              <Icon size={15} />
            </Option>
          ))}
        </Section>
      ) : null}

      {arrowKind !== undefined ? (
        <Section title="Arrow type">
          <Option active={arrowKind === 'elbow'} label="Elbow" onSelect={() => apply(ArrowShapeKindStyle, 'elbow')}>
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 4h6v10h6" />
            </svg>
          </Option>
          <Option active={arrowKind === 'arc'} label="Curved" onSelect={() => apply(ArrowShapeKindStyle, 'arc')}>
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
              <path d="M3 14C5 5 12 4 15 4" />
            </svg>
          </Option>
        </Section>
      ) : null}

      {headStart !== undefined ? (
        <Section title="Arrowhead start">
          {ARROWHEADS.map((head) => (
            <Option key={head} active={headStart === head} label={head} onSelect={() => apply(ArrowShapeArrowheadStartStyle, head)}>
              <ArrowheadIcon head={head} flip />
            </Option>
          ))}
        </Section>
      ) : null}

      {headEnd !== undefined ? (
        <Section title="Arrowhead end">
          {ARROWHEADS.map((head) => (
            <Option key={head} active={headEnd === head} label={head} onSelect={() => apply(ArrowShapeArrowheadEndStyle, head)}>
              <ArrowheadIcon head={head} flip={false} />
            </Option>
          ))}
        </Section>
      ) : null}

      {font !== undefined ? (
        <Section title="Font">
          {(
            [
              ['draw', 'Hand-drawn', "'tldraw_draw', cursive"],
              ['sans', 'Sans', "'tldraw_sans', sans-serif"],
              ['serif', 'Serif', "'tldraw_serif', serif"],
              ['mono', 'Code', "'tldraw_mono', monospace"],
            ] as const
          ).map(([value, label, family]) => (
            <Option key={value} active={font === value} label={label} onSelect={() => apply(DefaultFontStyle, value)}>
              <span style={{ fontFamily: family, fontSize: 13, fontWeight: 600 }}>Aa</span>
            </Option>
          ))}
        </Section>
      ) : null}

      {align !== undefined ? (
        <Section title="Text align">
          {(
            [
              ['start', 'Left', 'M3 5h12M3 9h8M3 13h10'],
              ['middle', 'Center', 'M3 5h12M5 9h8M4 13h10'],
              ['end', 'Right', 'M3 5h12M7 9h8M5 13h10'],
            ] as const
          ).map(([value, label, path]) => (
            <Option key={value} active={align === value} label={label} onSelect={() => apply(DefaultTextAlignStyle, value)}>
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
                <path d={path} />
              </svg>
            </Option>
          ))}
        </Section>
      ) : null}

      {opacity !== undefined ? (
        <div className="sp-section">
          <div className="sp-title">Opacity</div>
          <input
            type="range"
            className="sp-range"
            min={0}
            max={OPACITIES.length - 1}
            step={1}
            aria-label="Opacity"
            value={
              opacity.type === 'mixed'
                ? OPACITIES.length - 1
                : OPACITIES.findIndex((item) => Math.abs(item - opacity.value) < 0.01)
            }
            onChange={(event) => applyOpacity(OPACITIES[Number(event.target.value)])}
          />
          <div className="sp-range-labels">
            <span>10</span>
            <span>100</span>
          </div>
        </div>
      ) : null}
    </div>
  )
}

// On desktop the panel lives on the left (see MenuPanelWithStyles), so tldraw's top-right slot
// stays empty; small screens keep tldraw's own popover, which renders this with isMobile.
export default function StylePanel(props: TLUiStylePanelProps) {
  if (props.isMobile === true) {
    return <DefaultStylePanel {...props} />
  }
  return null
}

// Excalidraw-style placement: the style panel sits under the main menu in the top-left corner.
export function MenuPanelWithStyles() {
  const editor = useEditor()
  const breakpoint = useBreakpoint()
  const isReadonly = useReadonly()
  // Like Excalidraw, the panel only shows up while there is a selection to style.
  const hasSelection = useValue('has selection', () => editor.getSelectedShapeIds().length > 0, [editor])
  const showStyles = hasSelection && breakpoint >= PORTRAIT_BREAKPOINT.TABLET_SM && !isReadonly
  return (
    <>
      <DefaultMenuPanel />
      {showStyles ? (
        <DefaultStylePanel>
          <DrawdoroStylePanelContent />
        </DefaultStylePanel>
      ) : null}
    </>
  )
}
