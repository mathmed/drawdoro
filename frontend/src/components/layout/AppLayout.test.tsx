import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Diagram } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { advance, pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import { SLOW_LOAD_MS } from '../ui/loading/BrandLoader'
import AppLayout from './AppLayout'

vi.mock('../canvas/DrawingCanvas', () => ({
  default: ({ diagram }: { diagram: Diagram }) => <div data-testid="canvas">{diagram.name}</div>,
}))
vi.mock('../home/HomeView', () => ({ default: () => <div data-testid="home" /> }))
vi.mock('../sidebar/Sidebar', () => ({ default: () => null }))
vi.mock('../topbar/TopBar', () => ({ default: () => null }))
vi.mock('./Inspector', () => ({ default: () => null }))
vi.mock('../palette/CommandPalette', () => ({ default: () => null }))
vi.mock('../presentation/PresentationMode', () => ({ default: () => null }))
vi.mock('../semantic/ValidationModal', () => ({ default: () => null }))
vi.mock('../diagram/NewDiagramDialog', () => ({ default: () => null }))
vi.mock('../../hooks/useGlobalShortcuts', () => ({ useGlobalShortcuts: () => undefined }))

function diagram(id: string, name: string): Diagram {
  return { id, project_id: 'p1', folder_id: null, name, canvas_state: null, updated_at: '2026-01-01T10:00:00Z' }
}

beforeEach(() => {
  vi.useFakeTimers()
  useAppStore.setState(useAppStore.getInitialState(), true)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('AppLayout stage', () => {
  it('should show the overview when no diagram is being opened', () => {
    render(<AppLayout />)

    expect(screen.getByTestId('home')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('should show the brand loader while a diagram opens and fade it out over the canvas', async () => {
    const { container } = render(<AppLayout isOpeningDiagram />)
    expect(screen.queryByTestId('home')).not.toBeInTheDocument()
    expect(container.querySelector('.stage')).toHaveAttribute('aria-busy', 'true')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Test App: Opening diagram')

    act(() => useAppStore.setState({ activeDiagram: diagram('d1', 'Checkout') }))
    // The canvas mounts at once, under the loader that is still on its minimum time.
    expect(screen.getByTestId('canvas')).toHaveTextContent('Checkout')
    expect(container.querySelector('.loading-overlay')).toHaveAttribute('data-state', 'enter')

    await pastLoaderExit()
    expect(container.querySelector('.loading-overlay')).toBeNull()
    expect(container.querySelector('.stage')).toHaveAttribute('aria-busy', 'false')
  })

  it('should offer a retry when opening takes too long', async () => {
    const onRetry = vi.fn()
    render(<AppLayout isOpeningDiagram onRetryDiagram={onRetry} />)

    await advance(SLOW_LOAD_MS + 200)

    expect(screen.getByRole('status')).toHaveTextContent('This is taking longer than usual.')
    act(() => screen.getByRole('button', { name: 'Try again' }).click())
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('should keep the current canvas with a top progress bar while switching diagrams', async () => {
    useAppStore.setState({ activeDiagram: diagram('d1', 'Checkout'), isLoadingDiagram: true })
    render(<AppLayout isOpeningDiagram />)

    await advance(150)

    expect(screen.getByTestId('canvas')).toHaveTextContent('Checkout')
    expect(screen.getByRole('progressbar', { name: 'Opening diagram' })).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
