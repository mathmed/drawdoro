import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { LOADER_DELAY_MS } from '../../../hooks/useDelayedVisibility'
import BrandLoader from './BrandLoader'
import { BRAND_LOADER_HANDOFF_MS } from './brandLoaderRegistry'
import CanvasLoadingScreen from './CanvasLoadingScreen'

describe('CanvasLoadingScreen', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Lets the hand-off window of loaders left by earlier tests run out.
    vi.advanceTimersByTime(BRAND_LOADER_HANDOFF_MS)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should wait before showing the loader when nothing was loading', () => {
    const { container } = render(<CanvasLoadingScreen />)
    expect(container.querySelector('.canvas-loading')).toHaveAttribute('data-handoff', 'false')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS))

    expect(screen.getByRole('status')).toHaveTextContent('Opening diagram')
  })

  it('should take over at once from a loader already on screen', () => {
    const stage = render(<BrandLoader label="Opening diagram" />)

    const { container } = render(<CanvasLoadingScreen />)

    expect(container.querySelector('.canvas-loading')).toHaveAttribute('data-handoff', 'true')
    expect(container.querySelector('.brand-loader')).not.toBeNull()
    stage.unmount()
  })

  it('should take over at once from a loader that has just gone', () => {
    render(<BrandLoader label="Opening diagram" />).unmount()
    act(() => vi.advanceTimersByTime(BRAND_LOADER_HANDOFF_MS - 50))

    const { container } = render(<CanvasLoadingScreen />)

    expect(container.querySelector('.canvas-loading')).toHaveAttribute('data-handoff', 'true')
  })
})
