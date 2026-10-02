import { useState } from 'react'

import { LOADER_DELAY_MS, useDelayedVisibility } from '../../../hooks/useDelayedVisibility'
import BrandLoader from './BrandLoader'
import { isBrandLoaderOnScreen } from './brandLoaderRegistry'

// tldraw's LoadingScreen slot, shown while the canvas loads its fonts. It takes over straight away
// from a loader already on screen, so opening a diagram reads as one continuous loading state.
export default function CanvasLoadingScreen() {
  const [isHandoff] = useState(isBrandLoaderOnScreen)
  const visible = useDelayedVisibility(true, { delayMs: isHandoff ? 0 : LOADER_DELAY_MS })
  return (
    <div className="canvas-loading" data-handoff={isHandoff}>
      {visible ? <BrandLoader label="Opening diagram" /> : null}
    </div>
  )
}
