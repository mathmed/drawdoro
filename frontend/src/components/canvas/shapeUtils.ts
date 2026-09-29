import { ArrowShapeUtil } from 'tldraw'

import { CustomGeoShapeUtil } from '../../shapes/CustomGeoShapeUtil'

// Shared by the editor, the read-only share view and the /render page, so a diagram looks the
// same everywhere. Elbow arrows snap to the four side anchors of a shape; the wider radii make
// that snapping kick in before the pointer has to land exactly on the anchor.
export const shapeUtils = [
  CustomGeoShapeUtil,
  ArrowShapeUtil.configure({
    elbowArrowPointSnapDistance: 36,
    elbowArrowEdgeSnapDistance: 28,
    elbowArrowCenterSnapDistance: 32,
    arcArrowCenterSnapDistance: 24,
  }),
]
