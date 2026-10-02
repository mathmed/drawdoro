import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import TopProgressBar from './TopProgressBar'

describe('TopProgressBar', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should appear after a short delay as an indeterminate progress bar', () => {
    render(<TopProgressBar active label="Opening diagram" />)
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()

    act(() => vi.advanceTimersByTime(120))

    const bar = screen.getByRole('progressbar', { name: 'Opening diagram' })
    expect(bar).not.toHaveAttribute('aria-valuenow')
  })

  it('should not appear for quick work', () => {
    const { rerender } = render(<TopProgressBar active label="Loading" />)

    act(() => vi.advanceTimersByTime(60))
    rerender(<TopProgressBar active={false} label="Loading" />)
    act(() => vi.advanceTimersByTime(1000))

    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('should fade out and unmount once the work is done', () => {
    const { rerender } = render(<TopProgressBar active label="Loading" />)
    act(() => vi.advanceTimersByTime(120))

    rerender(<TopProgressBar active={false} label="Loading" />)
    act(() => vi.advanceTimersByTime(300))
    expect(screen.getByRole('progressbar')).toHaveAttribute('data-state', 'exit')

    act(() => vi.advanceTimersByTime(240))
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })
})
