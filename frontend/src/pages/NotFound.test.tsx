import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import NotFound from './NotFound'

describe('NotFound', () => {
  it('should explain the page is missing and link back home', () => {
    render(
      <MemoryRouter initialEntries={['/missing']}>
        <NotFound />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to Test App' })).toHaveAttribute('href', '/')
  })
})
