import type { ReactNode } from 'react'
import { PathBuilder, STROKE_SIZES, useDefaultColorTheme, type TLDefaultColorTheme, type TLGeoShape } from 'tldraw'

import { fillTintsFor, followsStroke, radiusFor, safeId, strokeColorOf, type DerivedFill } from './geoStyle'
import { sloppinessOffsetScale } from './sloppiness'

function derivedFill(hex: string, theme: TLDefaultColorTheme): DerivedFill {
  return fillTintsFor(hex, theme.id === 'dark')
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
export function CustomFill({ shape, d, scale }: { shape: TLGeoShape; d: string; scale: number }) {
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

export function RoundedBody({ shape, w, h, scale }: { shape: TLGeoShape; w: number; h: number; scale: number }) {
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
    outline = path.toSvg({
      style: 'draw',
      strokeWidth,
      randomSeed: shape.id,
      roundness,
      offsetScale: sloppinessOffsetScale(shape),
      props: { fill: 'none', stroke },
    })
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
