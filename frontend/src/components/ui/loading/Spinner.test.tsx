import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Spinner from './Spinner'

describe('Spinner', () => {
  it('should be decorative and sized by the size prop', () => {
    render(<Spinner size={18} className="extra" />)

    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveAttribute('aria-hidden', 'true')
    expect(spinner).toHaveAttribute('width', '18')
    expect(spinner).toHaveClass('spinner-ring', 'extra')
  })
})
