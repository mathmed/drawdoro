import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { LOADER_DELAY_MS, LOADER_MIN_VISIBLE_MS } from '../../../hooks/useDelayedVisibility'
import LoadingGate from './LoadingGate'

function Sut({ loading }: { loading: boolean }) {
  return (
    <LoadingGate loading={loading} fallback={<p>Loading</p>}>
      {() => <p>Content</p>}
    </LoadingGate>
  )
}

describe('LoadingGate', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should draw nothing at first, then the fallback, then the content', () => {
    const { rerender } = render(<Sut loading />)
    expect(screen.queryByText('Loading')).not.toBeInTheDocument()
    expect(screen.queryByText('Content')).not.toBeInTheDocument()

    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS))
    expect(screen.getByText('Loading')).toBeInTheDocument()

    rerender(<Sut loading={false} />)
    expect(screen.getByText('Loading')).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(LOADER_MIN_VISIBLE_MS))
    expect(screen.queryByText('Loading')).not.toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('should go straight to the content on a fast load', () => {
    const { rerender } = render(<Sut loading />)

    rerender(<Sut loading={false} />)

    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('should draw the placeholder during the appear delay', () => {
    render(
      <LoadingGate loading fallback={<p>Loading</p>} placeholder={<p>Reserved</p>}>
        <p>Content</p>
      </LoadingGate>,
    )

    expect(screen.getByText('Reserved')).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(LOADER_DELAY_MS))
    expect(screen.queryByText('Reserved')).not.toBeInTheDocument()
    expect(screen.getByText('Loading')).toBeInTheDocument()
  })

  it('should accept plain children', () => {
    render(
      <LoadingGate loading={false} fallback={null}>
        <p>Ready</p>
      </LoadingGate>,
    )

    expect(screen.getByText('Ready')).toBeInTheDocument()
  })
})
