import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Logo from './Logo'

describe('Logo', () => {
  it('should expose the product name as an accessible image when shown alone', () => {
    render(<Logo size={40} />)

    const mark = screen.getByRole('img', { name: 'Test App' })
    expect(mark).toHaveAttribute('width', '40')
    expect(screen.queryByText('Test App')).not.toBeInTheDocument()
  })

  it('should hide the mark from assistive tech when the wordmark is visible', () => {
    const { container } = render(<Logo withWordmark />)

    expect(screen.getByText('Test App')).toHaveClass('logo-wordmark')
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
  })

  it('should give each instance its own gradient id', () => {
    const { container } = render(
      <>
        <Logo />
        <Logo />
      </>,
    )

    const ids = [...container.querySelectorAll('linearGradient')].map((gradient) => gradient.id)
    expect(new Set(ids).size).toBe(2)
    container.querySelectorAll('svg').forEach((svg, index) => {
      expect(svg.querySelector('rect')).toHaveAttribute('fill', `url(#${ids[index]})`)
    })
  })
})
