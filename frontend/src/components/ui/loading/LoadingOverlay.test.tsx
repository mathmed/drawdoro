import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import LoadingOverlay, { OVERLAY_EXIT_MS } from './LoadingOverlay'

describe('LoadingOverlay', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should fade out before leaving the page', () => {
    const { rerender, container } = render(<LoadingOverlay visible>Loading</LoadingOverlay>)
    expect(container.querySelector('.loading-overlay')).toHaveAttribute('data-state', 'enter')

    rerender(<LoadingOverlay visible={false}>Loading</LoadingOverlay>)
    const overlay = container.querySelector('.loading-overlay')
    expect(overlay).toHaveAttribute('data-state', 'exit')
    expect(overlay).toHaveAttribute('aria-hidden', 'true')

    act(() => vi.advanceTimersByTime(OVERLAY_EXIT_MS))
    expect(screen.queryByText('Loading')).not.toBeInTheDocument()
  })

  it('should render nothing while hidden', () => {
    const { container } = render(<LoadingOverlay visible={false}>Loading</LoadingOverlay>)

    expect(container).toBeEmptyDOMElement()
  })
})
