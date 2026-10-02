import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { stubReducedMotion } from '../../../test/reducedMotion'
import BrandLoader, { SLOW_LOAD_MS } from './BrandLoader'

describe('BrandLoader', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should announce the label with the configured product name', () => {
    render(<BrandLoader label="Opening diagram" />)

    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-live', 'polite')
    expect(status).toHaveTextContent('Test App: Opening diagram')
  })

  it('should draw the product logo as decoration', () => {
    const { container } = render(<BrandLoader label="Loading" />)

    const mark = container.querySelector('.brand-loader-mark')
    expect(mark).toHaveAttribute('aria-hidden', 'true')
    expect(mark?.querySelector('.logo svg')).not.toBeNull()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('should show the product name only when asked', () => {
    const { rerender, container } = render(<BrandLoader label="Loading" />)
    expect(container.querySelector('.brand-loader-name')).toBeNull()

    rerender(<BrandLoader label="Loading" showName />)

    expect(container.querySelector('.brand-loader-name')).toHaveTextContent('Test App')
  })

  it('should add a hint and the retry action once the wait gets long', async () => {
    const onRetry = vi.fn()
    render(<BrandLoader label="Opening diagram" onRetry={onRetry} />)
    expect(screen.queryByText('This is taking longer than usual.')).not.toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()

    act(() => vi.advanceTimersByTime(SLOW_LOAD_MS))

    expect(screen.getByRole('status')).toHaveTextContent('This is taking longer than usual.')
    vi.useRealTimers()
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('should use a custom hint and threshold, and no retry without a handler', () => {
    render(<BrandLoader label="Loading" slowHint="Still working on it." slowAfterMs={1000} />)

    act(() => vi.advanceTimersByTime(1000))

    expect(screen.getByText('Still working on it.')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('should switch to the reduced-motion variant when the user asks for less motion', () => {
    const media = stubReducedMotion(false)
    const { container } = render(<BrandLoader label="Loading" />)
    expect(container.querySelector('.brand-loader')).toHaveAttribute('data-motion', 'full')

    act(() => media.setReduced(true))

    expect(container.querySelector('.brand-loader')).toHaveAttribute('data-motion', 'reduced')
  })

  it('should size the mark from the size prop', () => {
    const { container } = render(<BrandLoader label="Loading" size={64} />)

    expect(container.querySelector('.brand-loader')).toHaveStyle({ '--brand-loader-size': '64px' })
    expect(container.querySelector('.logo svg')).toHaveAttribute('width', '64')
  })

  it('should clear the slow-load timer on unmount', () => {
    const sut = render(<BrandLoader label="Loading" />)

    sut.unmount()

    expect(vi.getTimerCount()).toBe(0)
  })
})
