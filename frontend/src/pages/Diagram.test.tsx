import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Diagram } from '../api/types'
import { useAppStore } from '../store/useAppStore'
import DiagramPage from './Diagram'

vi.mock('../components/layout/AppLayout', () => ({
  default: ({ isOpeningDiagram }: { isOpeningDiagram: boolean }) => (
    <div data-testid="layout" data-opening={isOpeningDiagram} />
  ),
}))

const CHECKOUT: Diagram = { id: 'd1', project_id: 'p1', folder_id: null, name: 'Checkout', canvas_state: null, updated_at: '2026-01-01T10:00:00Z' }

function renderSut(): void {
  render(
    <MemoryRouter initialEntries={['/diagrams/d1']}>
      <Routes>
        <Route path="/diagrams/:id" element={<DiagramPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useAppStore.setState(useAppStore.getInitialState(), true)
})

describe('DiagramPage', () => {
  it('should keep the stage in its opening state until the load settles', async () => {
    let finish!: () => void
    const loadDiagram = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          finish = () => {
            useAppStore.setState({ activeDiagram: CHECKOUT })
            resolve()
          }
        }),
    )
    useAppStore.setState({ loadDiagram })
    renderSut()

    expect(screen.getByTestId('layout')).toHaveAttribute('data-opening', 'true')
    finish()
    await vi.waitFor(() => expect(screen.getByTestId('layout')).toHaveAttribute('data-opening', 'false'))
    expect(loadDiagram).toHaveBeenCalledWith('d1')
  })

  it('should let the user try again when the diagram could not be opened', async () => {
    const loadDiagram = vi
      .fn<(id: string) => Promise<void>>()
      .mockResolvedValueOnce(undefined)
      .mockImplementationOnce(async () => {
        useAppStore.setState({ activeDiagram: CHECKOUT })
      })
    useAppStore.setState({ loadDiagram })
    renderSut()

    expect(await screen.findByText('Diagram not found')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByTestId('layout')).toHaveAttribute('data-opening', 'false')
    expect(loadDiagram).toHaveBeenCalledTimes(2)
  })
})
