import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { DiagramSummary, Project, Workspace } from '../../api/types'
import { useWorkspacePresence } from '../../hooks/useWorkspacePresence'
import { useAppStore } from '../../store/useAppStore'
import { useWorkspacePresenceStore } from '../../store/useWorkspacePresenceStore'
import { pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import Sidebar from './Sidebar'

vi.mock('./SidebarFooter', () => ({ default: () => null }))
vi.mock('../../hooks/useWorkspacePresence', () => ({ useWorkspacePresence: vi.fn() }))

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
  useWorkspacePresenceStore.getState().reset()
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

describe('Sidebar presence', () => {
  const OTHER_PROJECT: Project = { ...PROJECT, id: 'p2', name: 'Antifraud' }
  const DIAGRAM: DiagramSummary = { id: 'd1', project_id: 'p1', folder_id: null, name: 'Architecture' }
  const ANA = { id: 'u-ana', name: 'Ana', kind: 'person' as const, picture_url: 'https://example.com/ana.png' }
  const BRUNO = { id: 'u-bruno', name: 'Bruno', kind: 'person' as const, picture_url: null }

  it('should show who is in each diagram and, even collapsed, in each project', () => {
    useAppStore.setState({
      isLoadingWorkspaces: false,
      workspaces: [WORKSPACE],
      activeWorkspace: WORKSPACE,
      projects: [PROJECT, OTHER_PROJECT],
      activeProject: PROJECT,
      diagrams: [DIAGRAM],
    })
    useWorkspacePresenceStore.getState().applySnapshot('u-me', [
      { diagramId: 'd1', projectId: 'p1', users: [ANA] },
      { diagramId: 'd9', projectId: 'p2', users: [ANA, BRUNO] },
    ])
    renderSut()

    expect(useWorkspacePresence).toHaveBeenLastCalledWith('w1')
    expect(screen.getByRole('group', { name: 'In this diagram now: Ana' })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'In this project now: Ana' })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'In this project now: Ana, Bruno' })).toBeInTheDocument()
  })

  it('should not subscribe before a workspace is chosen', () => {
    renderSut()
    expect(useWorkspacePresence).toHaveBeenLastCalledWith(null)
  })
})
