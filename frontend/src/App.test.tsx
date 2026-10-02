import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { useAppStore } from './store/useAppStore'
import { useAuthStore } from './store/useAuthStore'
import { pastLoaderDelay, pastLoaderExit } from './test/timers'

vi.mock('./pages/Landing', () => ({ default: () => <div data-testid="landing" /> }))
vi.mock('./pages/Home', () => ({ default: () => <div data-testid="home" /> }))
vi.mock('./pages/Diagram', () => ({ default: () => null }))
vi.mock('./pages/AuthCallback', () => ({ default: () => null }))
vi.mock('./pages/SharedDiagram', () => ({ default: () => null }))
vi.mock('./pages/RenderDiagram', () => ({ default: () => null }))
vi.mock('./pages/NotFound', () => ({ default: () => null }))
vi.mock('./components/ui/DialogHost', () => ({ default: () => null }))
vi.mock('./components/ui/Toaster', () => ({ default: () => null }))

beforeEach(() => {
  vi.useFakeTimers()
  useAuthStore.setState({ status: 'loading', initialize: vi.fn(async () => undefined) })
  useAppStore.setState({ loadWorkspaces: vi.fn(async () => undefined) })
})

afterEach(() => {
  vi.useRealTimers()
})

function renderSut() {
  return render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  )
}

describe('App boot', () => {
  it('should show the branded loader while the session is checked, then fade it out', async () => {
    const { container } = renderSut()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Checking your session')
    expect(container.querySelector('.brand-loader-name')).toHaveTextContent('Test App')

    act(() => useAuthStore.setState({ status: 'signed-out' }))
    // The landing page mounts straight away, under the fading loader.
    expect(screen.getByTestId('landing')).toBeInTheDocument()

    await pastLoaderExit()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('should not flash a loader when the session is known quickly', async () => {
    renderSut()

    act(() => useAuthStore.setState({ status: 'signed-in' }))
    await pastLoaderDelay()

    expect(screen.getByTestId('home')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
