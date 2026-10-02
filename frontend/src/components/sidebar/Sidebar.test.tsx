import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Project, Workspace } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import Sidebar from './Sidebar'

vi.mock('./SidebarFooter', () => ({ default: () => null }))

const WORKSPACE: Workspace = { id: 'w1', name: 'Platform', slug: 'platform', created_at: '2026-01-01T00:00:00Z' }
const PROJECT: Project = { id: 'p1', workspace_id: 'w1', name: 'Payments', description: null, created_at: '2026-01-01T00:00:00Z' }

function renderSut(): void {
  render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.useFakeTimers()
  useAppStore.setState(useAppStore.getInitialState(), true)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('Sidebar loading', () => {
  it('should show placeholder projects and workspace name while the workspace loads', async () => {
    renderSut()
    expect(screen.getByRole('button', { name: /Loading workspace/ })).toHaveAttribute('aria-busy', 'true')

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Loading projects')
    expect(screen.queryByText(/No projects/)).not.toBeInTheDocument()

    act(() =>
      useAppStore.setState({
        isLoadingWorkspaces: false,
        workspaces: [WORKSPACE],
        activeWorkspace: WORKSPACE,
        projects: [PROJECT],
      }),
    )
    await pastLoaderExit()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByText('Payments')).toBeInTheDocument()
    expect(screen.getByText('Platform')).toBeInTheDocument()
  })

  it('should show placeholder rows while the open project tree loads', async () => {
    useAppStore.setState({
      isLoadingWorkspaces: false,
      workspaces: [WORKSPACE],
      activeWorkspace: WORKSPACE,
      projects: [PROJECT],
      activeProject: PROJECT,
      isLoadingProject: true,
    })
    renderSut()

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Loading diagrams')
    expect(screen.queryByText(/No diagrams yet/)).not.toBeInTheDocument()

    act(() => useAppStore.setState({ isLoadingProject: false }))
    await pastLoaderExit()
    expect(screen.getByText(/No diagrams yet/)).toBeInTheDocument()
  })
})
