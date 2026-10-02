import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getSharedDiagram, type SharedDiagram } from '../api/diagrams'
import { pastLoaderDelay, pastLoaderExit } from '../test/timers'
import SharedDiagramPage from './SharedDiagram'

vi.mock('../api/diagrams', () => ({ getSharedDiagram: vi.fn() }))
vi.mock('../components/canvas/SharedCanvas', () => ({ default: () => <div data-testid="shared-canvas" /> }))

const SHARED = { id: 'd1', name: 'Checkout', canvas_state: null } as SharedDiagram

function renderSut(): void {
  render(
    <MemoryRouter initialEntries={['/share/token-1']}>
      <Routes>
        <Route path="/share/:token" element={<SharedDiagramPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SharedDiagramPage loading', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('should show the brand loader with the product name, then the diagram', async () => {
    vi.useFakeTimers()
    let resolve!: (diagram: SharedDiagram) => void
    vi.mocked(getSharedDiagram).mockReturnValue(new Promise((done) => (resolve = done)))
    const { container } = render(
      <MemoryRouter initialEntries={['/share/token-1']}>
        <Routes>
          <Route path="/share/:token" element={<SharedDiagramPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Opening shared diagram')
    expect(container.querySelector('.brand-loader-name')).toHaveTextContent('Test App')

    await act(async () => resolve(SHARED))
    await pastLoaderExit()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByTestId('shared-canvas')).toBeInTheDocument()
  })

  describe('when the link fails', () => {
    beforeEach(() => {
      vi.mocked(getSharedDiagram).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(SHARED)
    })

    it('should offer to try again', async () => {
      renderSut()

      expect(await screen.findByText('Shared diagram not found')).toBeInTheDocument()
      await userEvent.click(screen.getByRole('button', { name: 'Try again' }))

      expect(await screen.findByTestId('shared-canvas')).toBeInTheDocument()
      expect(getSharedDiagram).toHaveBeenCalledTimes(2)
    })
  })
})
