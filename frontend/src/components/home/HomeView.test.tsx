import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { DiagramSummary, Project, Workspace } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { advance, pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import HomeView from './HomeView'

const WORKSPACE: Workspace = { id: 'w1', name: 'Platform', slug: 'platform', created_at: '2026-01-01T00:00:00Z' }
const PROJECT: Project = { id: 'p1', workspace_id: 'w1', name: 'Payments', description: null, created_at: '2026-01-01T00:00:00Z' }
const CHECKOUT: DiagramSummary = { id: 'd1', project_id: 'p1', folder_id: null, name: 'Checkout', updated_at: '2026-01-01T10:00:00Z' }

function renderSut(): void {
  render(
    <MemoryRouter>
      <HomeView />
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

describe('HomeView loading', () => {
  it('should show the overview skeleton while workspaces load, then the project', async () => {
    renderSut()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Loading your workspace')

    useAppStore.setState({
      isLoadingWorkspaces: false,
      workspaces: [WORKSPACE],
      activeWorkspace: WORKSPACE,
      projects: [PROJECT],
      activeProject: PROJECT,
      diagrams: [CHECKOUT],
    })
    await pastLoaderExit()

    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Payments' })).toBeInTheDocument()
    expect(screen.getByText('Checkout')).toBeInTheDocument()
  })

  it('should skip the skeleton when the data arrives quickly', async () => {
    renderSut()
    await advance(50)

    useAppStore.setState({ isLoadingWorkspaces: false })
    await advance(0)

    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Welcome to Test App' })).toBeInTheDocument()
  })

  it('should not offer to create a first project while the projects are loading', async () => {
    useAppStore.setState({
      isLoadingWorkspaces: false,
      workspaces: [WORKSPACE],
      activeWorkspace: WORKSPACE,
      isLoadingProjects: true,
    })
    renderSut()

    await pastLoaderDelay()
    expect(screen.queryByText('Start your first project')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Loading your workspace')

    useAppStore.setState({ isLoadingProjects: false })
    await pastLoaderExit()
    expect(screen.getByText('Start your first project')).toBeInTheDocument()
  })

  it('should show placeholder cards while the project tree loads', async () => {
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
    expect(screen.getByRole('heading', { name: 'Payments' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Loading diagrams')
    expect(document.querySelectorAll('.diagram-card-skeleton')).toHaveLength(6)
    expect(screen.queryByText('No diagrams yet')).not.toBeInTheDocument()

    useAppStore.setState({ isLoadingProject: false, diagrams: [CHECKOUT] })
    await pastLoaderExit()
    expect(document.querySelector('.diagram-card-skeleton')).toBeNull()
    expect(screen.getByText('Checkout')).toBeInTheDocument()
  })
})
