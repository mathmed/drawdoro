import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createComment, listComments, setCommentResolved } from '../api/comments'
import { getDocumentation } from '../api/documentation'
import { deleteDiagram, getDiagramById, updateDiagram } from '../api/diagrams'
import { removeMember, listMembers } from '../api/members'
import { deleteProject, getProjectTree, listProjects } from '../api/projects'
import { listWorkspaces } from '../api/workspaces'
import type { Diagram, Project, ProjectTree, Workspace, WorkspaceMember } from '../api/types'
import { makeComment } from '../test/comments'
import { useAppStore } from './useAppStore'
import { useAuthStore } from './useAuthStore'

const authConfig = vi.hoisted(() => ({ enabled: false }))

vi.mock('../auth/config', () => ({ authConfig }))
vi.mock('../api/comments')
vi.mock('../api/documentation')
// toSummary is a pure helper the store relies on; only the HTTP calls are mocked.
vi.mock('../api/diagrams', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/diagrams')>()),
  deleteDiagram: vi.fn(),
  getDiagramById: vi.fn(),
  updateDiagram: vi.fn(),
}))
vi.mock('../api/members')
vi.mock('../api/projects')
vi.mock('../api/workspaces')

const LAST_WORKSPACE_KEY = 'test-app:last-workspace'
const LAST_PROJECT_KEY = 'test-app:last-project'

function workspace(id: string): Workspace {
  return { id, name: `Workspace ${id}`, slug: id, created_at: '2026-01-01T00:00:00Z' }
}

function project(id: string, workspaceId = 'w1'): Project {
  return { id, workspace_id: workspaceId, name: `Project ${id}`, description: null, created_at: '2026-01-01T00:00:00Z' }
}

function diagram(overrides: Partial<Diagram> = {}): Diagram {
  return {
    id: 'd1',
    project_id: 'p1',
    folder_id: 'f1',
    name: 'Checkout',
    canvas_state: { shapes: 1 },
    semantic_metadata: { s1: { type: 'service' } },
    updated_at: '2026-01-01T10:00:00Z',
    ...overrides,
  }
}

function member(overrides: Partial<WorkspaceMember> = {}): WorkspaceMember {
  return { user_id: 'u1', name: 'Ana', email: 'ana@example.com', role: 'editor', ...overrides }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => {
    resolve = done
  })
  return { promise, resolve }
}

beforeEach(() => {
  authConfig.enabled = false
  useAppStore.setState(useAppStore.getInitialState(), true)
  useAuthStore.setState({ status: 'signed-in', profile: null })
  vi.mocked(listProjects).mockResolvedValue([])
  vi.mocked(getProjectTree).mockResolvedValue({ folders: [], diagrams: [] })
  vi.mocked(getDocumentation).mockResolvedValue(null as never)
  vi.mocked(listComments).mockResolvedValue([])
  vi.mocked(listMembers).mockResolvedValue([])
})

describe('workspace and project selection', () => {
  it('should open the remembered workspace and project', async () => {
    localStorage.setItem(LAST_WORKSPACE_KEY, 'w2')
    localStorage.setItem(LAST_PROJECT_KEY, 'p2')
    vi.mocked(listWorkspaces).mockResolvedValue([workspace('w1'), workspace('w2')])
    vi.mocked(listProjects).mockResolvedValue([project('p1', 'w2'), project('p2', 'w2')])

    await useAppStore.getState().loadWorkspaces()

    const state = useAppStore.getState()
    expect(state.activeWorkspace?.id).toBe('w2')
    expect(state.activeProject?.id).toBe('p2')
    expect(state.isLoadingWorkspaces).toBe(false)
    expect(listProjects).toHaveBeenCalledWith('w2')
  })

  it('should fall back to the first workspace and project when nothing is remembered', async () => {
    localStorage.setItem(LAST_WORKSPACE_KEY, 'deleted')
    vi.mocked(listWorkspaces).mockResolvedValue([workspace('w1'), workspace('w2')])
    vi.mocked(listProjects).mockResolvedValue([project('p1'), project('p2')])

    await useAppStore.getState().loadWorkspaces()

    expect(useAppStore.getState().activeWorkspace?.id).toBe('w1')
    expect(useAppStore.getState().activeProject?.id).toBe('p1')
    expect(localStorage.getItem(LAST_WORKSPACE_KEY)).toBe('w1')
    expect(localStorage.getItem(LAST_PROJECT_KEY)).toBe('p1')
  })

  it('should stop loading even when listing workspaces fails', async () => {
    vi.mocked(listWorkspaces).mockRejectedValue(new Error('offline'))

    await expect(useAppStore.getState().loadWorkspaces()).rejects.toThrow('offline')

    expect(useAppStore.getState().isLoadingWorkspaces).toBe(false)
  })

  it('should ignore projects that arrive after the user switched workspace', async () => {
    const slow = deferred<Project[]>()
    vi.mocked(listProjects).mockImplementation((id) => (id === 'w1' ? slow.promise : Promise.resolve([project('p2', 'w2')])))

    const first = useAppStore.getState().setActiveWorkspace(workspace('w1'))
    await useAppStore.getState().setActiveWorkspace(workspace('w2'))
    slow.resolve([project('p1', 'w1')])
    await first

    const state = useAppStore.getState()
    expect(state.activeWorkspace?.id).toBe('w2')
    expect(state.projects.map((item) => item.id)).toEqual(['p2'])
    expect(state.activeProject?.id).toBe('p2')
  })

  it('should flag the project list as loading while a workspace opens', async () => {
    const slow = deferred<Project[]>()
    vi.mocked(listProjects).mockReturnValue(slow.promise)

    const pending = useAppStore.getState().setActiveWorkspace(workspace('w1'))

    expect(useAppStore.getState()).toMatchObject({ projects: [], isLoadingProjects: true })
    slow.resolve([])
    await pending
    expect(useAppStore.getState().isLoadingProjects).toBe(false)
  })

  it('should stop loading the project list when it fails', async () => {
    vi.mocked(listProjects).mockRejectedValue(new Error('offline'))

    await expect(useAppStore.getState().setActiveWorkspace(workspace('w1'))).rejects.toThrow('offline')

    expect(useAppStore.getState().isLoadingProjects).toBe(false)
  })

  it('should keep the newer workspace loading when an older list arrives', async () => {
    const slow = deferred<Project[]>()
    const newer = deferred<Project[]>()
    vi.mocked(listProjects).mockImplementation((id) => (id === 'w1' ? slow.promise : newer.promise))

    const first = useAppStore.getState().setActiveWorkspace(workspace('w1'))
    const second = useAppStore.getState().setActiveWorkspace(workspace('w2'))
    slow.resolve([project('p1', 'w1')])
    await first

    expect(useAppStore.getState().isLoadingProjects).toBe(true)
    newer.resolve([])
    await second
    expect(useAppStore.getState().isLoadingProjects).toBe(false)
  })

  it('should clear the previous project tree right away when switching project', async () => {
    useAppStore.setState({ activeProject: project('p1'), folders: [{ id: 'f1', project_id: 'p1', parent_folder_id: null, name: 'Old' }] })
    const slow = deferred<ProjectTree>()
    vi.mocked(getProjectTree).mockReturnValue(slow.promise)

    const pending = useAppStore.getState().setActiveProject(project('p2'))

    expect(useAppStore.getState()).toMatchObject({ folders: [], diagrams: [], isLoadingProject: true })
    slow.resolve({ folders: [], diagrams: [diagram({ project_id: 'p2' })] })
    await pending
    expect(useAppStore.getState().diagrams).toHaveLength(1)
    expect(useAppStore.getState().isLoadingProject).toBe(false)
  })

  it('should move to the next project when the active one is deleted', async () => {
    localStorage.setItem(LAST_PROJECT_KEY, 'p1')
    useAppStore.setState({ projects: [project('p1'), project('p2')], activeProject: project('p1') })
    vi.mocked(deleteProject).mockResolvedValue(undefined)

    await useAppStore.getState().deleteProject(project('p1'))

    expect(useAppStore.getState().projects.map((item) => item.id)).toEqual(['p2'])
    expect(useAppStore.getState().activeProject?.id).toBe('p2')
    expect(localStorage.getItem(LAST_PROJECT_KEY)).toBe('p2')
  })

  it('should close the open diagram when its project is deleted', async () => {
    useAppStore.setState({ projects: [project('p1')], activeProject: project('p1'), activeDiagram: diagram() })
    vi.mocked(deleteProject).mockResolvedValue(undefined)

    await useAppStore.getState().deleteProject(project('p1'))

    expect(useAppStore.getState()).toMatchObject({ activeDiagram: null, activeProject: null, projects: [] })
    expect(localStorage.getItem(LAST_PROJECT_KEY)).toBeNull()
  })
})

describe('saving diagrams', () => {
  it('should send the full diagram with only the changed field overridden', async () => {
    const current = diagram()
    useAppStore.setState({ activeProject: project('p1'), activeDiagram: current, diagrams: [current] })
    vi.mocked(updateDiagram).mockResolvedValue({ ...current, name: 'Payments', updated_at: '2026-01-01T11:00:00Z' })

    await useAppStore.getState().renameDiagram('Payments')

    expect(updateDiagram).toHaveBeenCalledWith('p1', 'd1', {
      name: 'Payments',
      folder_id: 'f1',
      canvas_state: { shapes: 1 },
      semantic_metadata: { s1: { type: 'service' } },
    })
    expect(useAppStore.getState().activeDiagram?.name).toBe('Payments')
    expect(useAppStore.getState().diagrams[0].name).toBe('Payments')
    expect(useAppStore.getState().saveStatus).toBe('saved')
  })

  it('should rename a diagram other than the open one', async () => {
    const open = diagram()
    const other = diagram({ id: 'd2', name: 'Other' })
    useAppStore.setState({ activeProject: project('p1'), activeDiagram: open, diagrams: [open, other] })
    vi.mocked(getDiagramById).mockResolvedValue(other)
    vi.mocked(updateDiagram).mockResolvedValue({ ...other, name: 'Renamed' })

    await useAppStore.getState().renameDiagram('Renamed', other)

    expect(getDiagramById).toHaveBeenCalledWith('d2')
    expect(updateDiagram).toHaveBeenCalledWith('p1', 'd2', expect.objectContaining({ name: 'Renamed' }))
    expect(useAppStore.getState().activeDiagram).toBe(open)
    expect(useAppStore.getState().diagrams.map((item) => item.name)).toEqual(['Checkout', 'Renamed'])
  })

  it('should do nothing when no diagram is open', async () => {
    await useAppStore.getState().saveCanvasState({})

    expect(updateDiagram).not.toHaveBeenCalled()
    expect(useAppStore.getState().saveStatus).toBe('idle')
  })

  it('should keep a newer copy pushed while the save was in flight', async () => {
    const current = diagram()
    useAppStore.setState({ activeProject: project('p1'), activeDiagram: current, diagrams: [current] })
    const save = deferred<Diagram>()
    vi.mocked(updateDiagram).mockReturnValue(save.promise)

    const pending = useAppStore.getState().saveCanvasState({ shapes: 2 })
    useAppStore.getState().applyPushedDiagram({ ...current, canvas_state: { shapes: 3 }, updated_at: '2026-01-01T12:00:00Z' })
    save.resolve({ ...current, canvas_state: { shapes: 2 }, updated_at: '2026-01-01T11:00:00Z' })
    await pending

    expect(useAppStore.getState().activeDiagram?.canvas_state).toEqual({ shapes: 3 })
    expect(useAppStore.getState().diagrams[0].updated_at).toBe('2026-01-01T12:00:00Z')
  })

  it('should stay "saving" until every overlapping save finished', async () => {
    const current = diagram()
    useAppStore.setState({ activeProject: project('p1'), activeDiagram: current, diagrams: [current] })
    const first = deferred<Diagram>()
    const second = deferred<Diagram>()
    vi.mocked(updateDiagram).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise)

    const saves = [useAppStore.getState().saveCanvasState({ a: 1 }), useAppStore.getState().saveCanvasState({ a: 2 })]
    first.resolve(current)
    await saves[0]

    expect(useAppStore.getState().saveStatus).toBe('saving')
    second.resolve(current)
    await saves[1]
    expect(useAppStore.getState().saveStatus).toBe('saved')
  })

  it('should flag the error and rethrow when the save fails', async () => {
    useAppStore.setState({ activeDiagram: diagram() })
    vi.mocked(updateDiagram).mockRejectedValue(new Error('500'))

    await expect(useAppStore.getState().saveCanvasState({})).rejects.toThrow('500')

    expect(useAppStore.getState().saveStatus).toBe('error')
  })

  it('should save the semantic metadata edited in the panel', async () => {
    const current = diagram()
    useAppStore.setState({ activeDiagram: current, semanticMetadata: {} })
    vi.mocked(updateDiagram).mockResolvedValue(current)

    useAppStore.getState().updateShapeMetadata('s1', { type: 'database' })
    useAppStore.getState().updateShapeMetadata('s1', { label: 'Orders DB' })
    await useAppStore.getState().saveSemanticMetadata()

    expect(updateDiagram).toHaveBeenCalledWith(
      'p1',
      'd1',
      expect.objectContaining({ semantic_metadata: { s1: { type: 'database', label: 'Orders DB' } } }),
    )
  })
})

describe('applyPushedDiagram', () => {
  it('should reject a push for another diagram', () => {
    useAppStore.setState({ activeDiagram: diagram() })

    const applied = useAppStore.getState().applyPushedDiagram({ ...diagram({ id: 'd2' }) })

    expect(applied).toBe(false)
    expect(useAppStore.getState().activeDiagram?.id).toBe('d1')
  })

  it('should reject a push older than the local copy', () => {
    useAppStore.setState({ activeDiagram: diagram() })

    const applied = useAppStore.getState().applyPushedDiagram({ ...diagram({ name: 'Stale', updated_at: '2026-01-01T09:00:00Z' }) })

    expect(applied).toBe(false)
    expect(useAppStore.getState().activeDiagram?.name).toBe('Checkout')
  })

  it('should keep unsaved panel edits when the pushed metadata did not change', () => {
    const current = diagram()
    useAppStore.setState({
      activeProject: project('p1'),
      activeDiagram: current,
      diagrams: [current],
      semanticMetadata: { s1: { type: 'queue' } },
    })

    const applied = useAppStore
      .getState()
      .applyPushedDiagram({ ...current, name: 'Renamed elsewhere', updated_at: '2026-01-01T11:00:00Z' })

    expect(applied).toBe(true)
    expect(useAppStore.getState().activeDiagram?.name).toBe('Renamed elsewhere')
    expect(useAppStore.getState().diagrams[0].name).toBe('Renamed elsewhere')
    expect(useAppStore.getState().semanticMetadata).toEqual({ s1: { type: 'queue' } })
  })

  it('should replace the panel metadata when someone else changed it', () => {
    const current = diagram()
    useAppStore.setState({ activeDiagram: current, semanticMetadata: { s1: { type: 'queue' } } })

    useAppStore.getState().applyPushedDiagram({ ...current, semantic_metadata: { s1: { type: 'cache' } } })

    expect(useAppStore.getState().semanticMetadata).toEqual({ s1: { type: 'cache' } })
  })
})

describe('opening diagrams', () => {
  it('should reset the diagram context and ignore stale documentation', async () => {
    const slow = deferred<never>()
    vi.mocked(getDocumentation).mockReturnValueOnce(slow.promise)
    useAppStore.setState({ activeElementId: 's9', validationResults: [{ severity: 'error', message: 'x', shapeIds: [] }] })

    const first = useAppStore.getState().setActiveDiagram(diagram())
    expect(useAppStore.getState()).toMatchObject({
      activeElementId: null,
      validationResults: [],
      semanticMetadata: { s1: { type: 'service' } },
      saveStatus: 'idle',
    })
    await useAppStore.getState().setActiveDiagram(diagram({ id: 'd2' }))
    slow.resolve({ id: 'doc-1', diagram_id: 'd1', content: 'old' } as never)
    await first

    expect(useAppStore.getState().activeDiagram?.id).toBe('d2')
    expect(useAppStore.getState().documentation).toBeNull()
  })

  it('should flag the documentation and comments as loading until they arrive', async () => {
    const slow = deferred<never>()
    vi.mocked(getDocumentation).mockReturnValueOnce(slow.promise)

    const pending = useAppStore.getState().setActiveDiagram(diagram())

    expect(useAppStore.getState().isLoadingDiagramDetails).toBe(true)
    slow.resolve(null as never)
    await pending
    expect(useAppStore.getState().isLoadingDiagramDetails).toBe(false)
  })

  it('should stop loading the details when they fail', async () => {
    vi.mocked(listComments).mockRejectedValueOnce(new Error('offline'))

    await expect(useAppStore.getState().setActiveDiagram(diagram())).rejects.toThrow('offline')

    expect(useAppStore.getState().isLoadingDiagramDetails).toBe(false)
  })

  it('should leave the details of a newer diagram loading when an older one settles', async () => {
    const slow = deferred<never>()
    const newer = deferred<never>()
    vi.mocked(getDocumentation).mockReturnValueOnce(slow.promise).mockReturnValueOnce(newer.promise)

    const first = useAppStore.getState().setActiveDiagram(diagram())
    const second = useAppStore.getState().setActiveDiagram(diagram({ id: 'd2' }))
    slow.resolve(null as never)
    await first

    expect(useAppStore.getState().isLoadingDiagramDetails).toBe(true)
    newer.resolve(null as never)
    await second
    expect(useAppStore.getState().isLoadingDiagramDetails).toBe(false)
  })

  it('should stop loading the details when the diagram is closed', () => {
    useAppStore.setState({ activeDiagram: diagram(), isLoadingDiagramDetails: true })

    useAppStore.getState().closeDiagram()

    expect(useAppStore.getState().isLoadingDiagramDetails).toBe(false)
  })

  it('should apply only the latest attempt when the same diagram is requested again', async () => {
    useAppStore.setState({ activeProject: project('p1') })
    const firstAttempt = deferred<Diagram>()
    const retry = deferred<Diagram>()
    vi.mocked(getDiagramById).mockReturnValueOnce(firstAttempt.promise).mockReturnValueOnce(retry.promise)

    const first = useAppStore.getState().loadDiagram('d1')
    const second = useAppStore.getState().loadDiagram('d1')
    firstAttempt.resolve(diagram({ name: 'Stale' }))
    await first

    expect(useAppStore.getState()).toMatchObject({ activeDiagram: null, isLoadingDiagram: true })
    retry.resolve(diagram({ name: 'Fresh' }))
    await second
    expect(useAppStore.getState().activeDiagram?.name).toBe('Fresh')
    expect(useAppStore.getState().isLoadingDiagram).toBe(false)
    expect(getDocumentation).toHaveBeenCalledTimes(1)
  })

  it('should stop loading when the diagram cannot be fetched', async () => {
    vi.mocked(getDiagramById).mockRejectedValueOnce(new Error('offline'))

    await useAppStore.getState().loadDiagram('d1')

    expect(useAppStore.getState()).toMatchObject({ activeDiagram: null, isLoadingDiagram: false })
  })

  it('should drop a load that finishes after the diagram was closed', async () => {
    useAppStore.setState({ activeProject: project('p1') })
    const slow = deferred<Diagram>()
    vi.mocked(getDiagramById).mockReturnValueOnce(slow.promise)

    const pending = useAppStore.getState().loadDiagram('d1')
    useAppStore.getState().closeDiagram()
    slow.resolve(diagram())
    await pending

    expect(useAppStore.getState()).toMatchObject({ activeDiagram: null, isLoadingDiagram: false })
  })

  it('should find a diagram by id across workspaces on direct navigation', async () => {
    vi.mocked(listWorkspaces).mockResolvedValue([workspace('w1'), workspace('w2')])
    vi.mocked(listProjects).mockImplementation(async (id) => (id === 'w1' ? [project('p1', 'w1')] : [project('p2', 'w2')]))
    vi.mocked(getDiagramById).mockResolvedValue(diagram({ id: 'target', project_id: 'p2' }))

    await useAppStore.getState().loadDiagram('target')

    const state = useAppStore.getState()
    expect(state.activeWorkspace?.id).toBe('w2')
    expect(state.activeProject?.id).toBe('p2')
    expect(state.activeDiagram?.id).toBe('target')
    expect(getProjectTree).toHaveBeenCalledWith('p2')
    expect(state.isLoadingDiagram).toBe(false)
    expect(localStorage.getItem(LAST_WORKSPACE_KEY)).toBe('w2')
    expect(localStorage.getItem(LAST_PROJECT_KEY)).toBe('p2')
  })

  it('should not reload the diagram that is already open', async () => {
    useAppStore.setState({ activeDiagram: diagram() })

    await useAppStore.getState().loadDiagram('d1')

    expect(listWorkspaces).not.toHaveBeenCalled()
    expect(getDocumentation).not.toHaveBeenCalled()
  })

  it('should close the open diagram when it is deleted', async () => {
    const current = diagram()
    useAppStore.setState({ activeProject: project('p1'), activeDiagram: current, diagrams: [current, diagram({ id: 'd2' })] })
    vi.mocked(deleteDiagram).mockResolvedValue(undefined)

    await useAppStore.getState().deleteDiagram(current)

    expect(useAppStore.getState().activeDiagram).toBeNull()
    expect(useAppStore.getState().diagrams.map((item) => item.id)).toEqual(['d2'])
  })
})

describe('members', () => {
  it('should skip members when login is disabled', async () => {
    useAppStore.setState({ activeWorkspace: workspace('w1'), myRole: 'owner' })

    await useAppStore.getState().loadMembers('w1')

    expect(listMembers).not.toHaveBeenCalled()
    expect(useAppStore.getState()).toMatchObject({ members: [], myRole: null })
  })

  it('should derive my role from the signed-in email', async () => {
    authConfig.enabled = true
    useAuthStore.setState({ profile: { email: 'Ana@Example.com', name: 'Ana' } })
    useAppStore.setState({ activeWorkspace: workspace('w1') })
    vi.mocked(listMembers).mockResolvedValue([member({ user_id: 'u2', email: 'bia@example.com', role: 'owner' }), member()])

    await useAppStore.getState().loadMembers('w1')

    expect(useAppStore.getState().myRole).toBe('editor')
    expect(useAppStore.getState().members).toHaveLength(2)
  })

  it('should flag members as loading until the list arrives', async () => {
    authConfig.enabled = true
    useAppStore.setState({ activeWorkspace: workspace('w1') })
    const slow = deferred<WorkspaceMember[]>()
    vi.mocked(listMembers).mockReturnValue(slow.promise)

    const pending = useAppStore.getState().loadMembers('w1')

    expect(useAppStore.getState().isLoadingMembers).toBe(true)
    slow.resolve([member()])
    await pending
    expect(useAppStore.getState().isLoadingMembers).toBe(false)
  })

  it('should stop loading members when the list fails', async () => {
    authConfig.enabled = true
    useAppStore.setState({ activeWorkspace: workspace('w1') })
    vi.mocked(listMembers).mockRejectedValue(new Error('offline'))

    await expect(useAppStore.getState().loadMembers('w1')).rejects.toThrow('offline')

    expect(useAppStore.getState().isLoadingMembers).toBe(false)
  })

  it('should drop members that arrive after switching workspace', async () => {
    authConfig.enabled = true
    useAppStore.setState({ activeWorkspace: workspace('w2') })
    vi.mocked(listMembers).mockResolvedValue([member()])

    await useAppStore.getState().loadMembers('w1')

    expect(useAppStore.getState().members).toEqual([])
  })

  it('should leave the workspace and reload the list when removing myself', async () => {
    authConfig.enabled = true
    useAuthStore.setState({ profile: { email: 'ana@example.com', name: 'Ana' } })
    useAppStore.setState({ activeWorkspace: workspace('w1'), members: [member()], myRole: 'editor', activeDiagram: diagram() })
    vi.mocked(removeMember).mockResolvedValue(undefined)
    vi.mocked(listWorkspaces).mockResolvedValue([workspace('w2')])

    await useAppStore.getState().removeMember('u1')

    expect(useAppStore.getState().activeDiagram).toBeNull()
    expect(useAppStore.getState().workspaces.map((item) => item.id)).toEqual(['w2'])
    expect(useAppStore.getState().activeWorkspace?.id).toBe('w2')
  })

  it('should reload members when removing someone else', async () => {
    authConfig.enabled = true
    useAuthStore.setState({ profile: { email: 'ana@example.com', name: 'Ana' } })
    useAppStore.setState({ activeWorkspace: workspace('w1'), members: [member(), member({ user_id: 'u2', email: 'bia@example.com' })] })
    vi.mocked(removeMember).mockResolvedValue(undefined)
    vi.mocked(listMembers).mockResolvedValue([member()])

    await useAppStore.getState().removeMember('u2')

    expect(listWorkspaces).not.toHaveBeenCalled()
    expect(useAppStore.getState().activeWorkspace?.id).toBe('w1')
    expect(useAppStore.getState().members).toEqual([member()])
  })
})

describe('ui state', () => {
  it('should open the comments tab for an element', () => {
    useAppStore.getState().commentOnElement('shape:1')

    expect(useAppStore.getState()).toMatchObject({ activeElementId: 'shape:1', inspectorTab: 'comments', isInspectorOpen: true })
  })

  it('should toggle panels', () => {
    useAppStore.getState().toggleSidebar()
    useAppStore.getState().toggleInspector()

    expect(useAppStore.getState()).toMatchObject({ isSidebarOpen: false, isInspectorOpen: true })
  })

  it('should open validation with no results when there is no editor', () => {
    useAppStore.getState().runValidation()

    expect(useAppStore.getState()).toMatchObject({ validationResults: [], isValidationOpen: true })
  })
})

describe('comments', () => {
  const COMMENT = makeComment({ id: 'c1' })

  it('should keep the comments of the open diagram only', async () => {
    useAppStore.setState({ activeDiagram: diagram({ id: 'd2' }), comments: [] })
    vi.mocked(listComments).mockResolvedValue([COMMENT])

    await useAppStore.getState().loadComments('d1')
    expect(useAppStore.getState().comments).toEqual([])

    await useAppStore.getState().loadComments('d2')
    expect(useAppStore.getState().comments).toEqual([COMMENT])
  })

  it('should not list a new comment twice when the realtime reload got it first', async () => {
    useAppStore.setState({ activeDiagram: diagram(), comments: [COMMENT] })
    vi.mocked(createComment).mockResolvedValue(COMMENT)

    await useAppStore.getState().addComment('shape:a', 'Missing the queue')

    expect(createComment).toHaveBeenCalledWith('d1', 'shape:a', 'Missing the queue')
    expect(useAppStore.getState().comments).toEqual([COMMENT])
  })

  it('should replace a comment with its resolved version', async () => {
    const other = makeComment({ id: 'c2' })
    const resolved = { ...COMMENT, resolved: true, resolved_at: '2026-01-01T12:00:00Z' }
    useAppStore.setState({ activeDiagram: diagram(), comments: [COMMENT, other] })
    vi.mocked(setCommentResolved).mockResolvedValue(resolved)

    await useAppStore.getState().setCommentResolved('c1', true)

    expect(setCommentResolved).toHaveBeenCalledWith('d1', 'c1', true)
    expect(useAppStore.getState().comments).toEqual([resolved, other])
  })

  it('should do nothing without an open diagram', async () => {
    useAppStore.setState({ activeDiagram: null })
    vi.mocked(setCommentResolved).mockClear()

    await useAppStore.getState().setCommentResolved('c1', true)

    expect(setCommentResolved).not.toHaveBeenCalled()
  })
})
