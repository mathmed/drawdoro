import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { startLogin } from '../auth/session'
import Landing from './Landing'

vi.mock('../auth/session', () => ({ startLogin: vi.fn() }))

function renderAt(path: string): void {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Landing />
    </MemoryRouter>,
  )
}

describe('Landing', () => {
  beforeEach(() => {
    vi.mocked(startLogin).mockResolvedValue(undefined)
  })

  it('should present the product by its configured name', () => {
    renderAt('/')

    expect(screen.getByText('Test App', { selector: '.logo-wordmark' })).toBeInTheDocument()
    expect(screen.getByText(/Test App brings architecture diagrams/)).toBeInTheDocument()
  })

  it('should start the login returning to the page the visitor opened', async () => {
    renderAt('/diagrams/42?tab=docs')

    await userEvent.click(screen.getByRole('button', { name: /Continue with Google/ }))

    expect(startLogin).toHaveBeenCalledExactlyOnceWith('/diagrams/42?tab=docs')
  })

  it('should return to the home page instead of the auth callback', async () => {
    renderAt('/auth/callback')

    await userEvent.click(screen.getByRole('button', { name: /Continue with Google/ }))

    expect(startLogin).toHaveBeenCalledExactlyOnceWith('/')
  })

  it('should disable the button while redirecting so the login is not started twice', async () => {
    renderAt('/')
    const button = screen.getByRole('button', { name: /Continue with Google/ })

    await userEvent.click(button)
    await userEvent.click(button)

    expect(button).toBeDisabled()
    expect(startLogin).toHaveBeenCalledOnce()
  })
})
