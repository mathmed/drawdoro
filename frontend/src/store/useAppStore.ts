import type { Editor } from 'tldraw'
import { create } from 'zustand'

import { authConfig } from '../auth/config'
import { storageKey } from '../config/branding'

import { createComment as apiCreateComment, listComments } from '../api/comments'
import { getDocumentation, upsertDocumentation } from '../api/documentation'
import {
  createDiagram as apiCreateDiagram,
  deleteDiagram as apiDeleteDiagram,
  listDiagrams,
  updateDiagram,
  type UpdateDiagramInput,
} from '../api/diagrams'
import {
  createFolder as apiCreateFolder,
  deleteFolder as apiDeleteFolder,
  listFolders,
  updateFolder as apiUpdateFolder,
} from '../api/folders'
import {
  createProject as apiCreateProject,
  deleteProject as apiDeleteProject,
  listProjects,
  updateProject as apiUpdateProject,
} from '../api/projects'
import {
  addMember as apiAddMember,
  listMembers,
  removeMember as apiRemoveMember,
  updateMemberRole as apiUpdateMemberRole,
} from '../api/members'
import { createWorkspace as apiCreateWorkspace, listWorkspaces } from '../api/workspaces'
import type {
  CanvasState,
  Comment,
  Diagram,
  DocumentationPage,
  Folder,
  Project,
  PushedDiagram,
  SemanticMetadata,
  ShapeMetadata,
  ValidationResult,
  Workspace,
  WorkspaceMember,
  WorkspaceRole,
} from '../api/types'
import { isOlder } from '../utils/freshness'
import { buildArchitectureGraph, validateArchitecture } from '../utils/validateArchitecture'
import type { Presence } from '../hooks/useRealtime'
import { useAuthStore } from './useAuthStore'

const EMPTY_PRESENCE: Presence = { users: [], you: null }

export type InspectorTab = 'properties' | 'docs' | 'comments' | 'gallery'
export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

const LAST_WORKSPACE_KEY = storageKey('last-workspace')
const LAST_PROJECT_KEY = storageKey('last-project')

function remember(key: string, value: string | null): void {
  try {
    if (value === null) {
      localStorage.removeItem(key)
    } else {
      localStorage.setItem(key, value)
    }
  } catch {
    // Remembering the last selection is a convenience; ignore unavailable storage.
  }
}

function recall(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

let pendingSaves = 0

interface AppState {
  workspaces: Workspace[]
  activeWorkspace: Workspace | null
  projects: Project[]
  activeProject: Project | null
  folders: Folder[]
  diagrams: Diagram[]
  activeDiagram: Diagram | null
  isLoadingWorkspaces: boolean
  isLoadingProject: boolean
  isLoadingDiagram: boolean
  saveStatus: SaveStatus
  documentation: DocumentationPage | null
  editor: Editor | null
  isSidebarOpen: boolean
  isInspectorOpen: boolean
  inspectorTab: InspectorTab
  isCommandPaletteOpen: boolean
  isValidationOpen: boolean
  newDiagramDialog: { folderId?: string } | null
  comments: Comment[]
  activeElementId: string | null
  isPresentationMode: boolean
  semanticMetadata: Record<string, ShapeMetadata>
  validationResults: ValidationResult[]
  presence: Presence
  members: WorkspaceMember[]
  // The signed-in user's role in the active workspace; null when login is disabled.
  myRole: WorkspaceRole | null

  loadWorkspaces: () => Promise<void>
  setActiveWorkspace: (workspace: Workspace) => Promise<void>
  setActiveProject: (project: Project) => Promise<void>
  setActiveDiagram: (diagram: Diagram) => Promise<void>
  closeDiagram: () => void
  loadDiagram: (diagramId: string) => Promise<void>
  createWorkspace: (name: string, slug: string) => Promise<void>
  createProject: (name: string) => Promise<Project | null>
  renameProject: (project: Project, name: string) => Promise<void>
  deleteProject: (project: Project) => Promise<void>
  createFolder: (name: string, parentId?: string) => Promise<void>
  renameFolder: (folder: Folder, name: string) => Promise<void>
  deleteFolder: (folder: Folder) => Promise<void>
  createDiagram: (name: string, folderId?: string) => Promise<Diagram | null>
  renameDiagram: (name: string, diagram?: Diagram) => Promise<void>
  deleteDiagram: (diagram: Diagram) => Promise<void>
  saveCanvasState: (state: CanvasState) => Promise<void>
  // Returns false when the pushed diagram is not the one open or is older than the local copy.
  applyPushedDiagram: (diagram: PushedDiagram) => boolean
  saveDocumentation: (content: string) => Promise<void>
  setEditor: (editor: Editor | null) => void
  toggleSidebar: () => void
  toggleInspector: () => void
  openInspector: (tab: InspectorTab) => void
  closeInspector: () => void
  setCommandPaletteOpen: (open: boolean) => void
  openNewDiagram: (folderId?: string) => void
  closeNewDiagram: () => void
  loadComments: (diagramId: string) => Promise<void>
  addComment: (elementId: string, content: string) => Promise<void>
  setActiveElement: (id: string | null) => void
  commentOnElement: (id: string) => void
  enterPresentation: () => void
  exitPresentation: () => void
  updateShapeMetadata: (shapeId: string, metadata: Partial<ShapeMetadata>) => void
  saveSemanticMetadata: () => Promise<void>
  runValidation: () => void
  closeValidation: () => void
  setPresence: (presence: Presence) => void
  loadMembers: (workspaceId: string) => Promise<void>
  addMember: (email: string, role: WorkspaceRole) => Promise<void>
  updateMemberRole: (userId: string, role: WorkspaceRole) => Promise<void>
  removeMember: (userId: string) => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => {
  // The backend PUT replaces every field, so each save sends the full current diagram
  // with only the changed fields overridden.
  async function persistDiagram(patch: Partial<UpdateDiagramInput>, target?: Diagram): Promise<void> {
    const diagram = target ?? get().activeDiagram
    if (diagram === null) {
      return
    }
    pendingSaves += 1
    set({ saveStatus: 'saving' })
    try {
      const updated = await updateDiagram(diagram.project_id, diagram.id, {
        name: diagram.name,
        folder_id: diagram.folder_id,
        canvas_state: diagram.canvas_state,
        semantic_metadata: diagram.semantic_metadata ?? null,
        ...patch,
      })
      // A newer copy may have been pushed by another writer while this save was in flight.
      const keepNewest = (item: Diagram) =>
        item.id === updated.id && !isOlder(updated.updated_at, item.updated_at) ? updated : item
      const current = get().activeDiagram
      set({
        activeDiagram: current === null ? null : keepNewest(current),
        diagrams: get().diagrams.map(keepNewest),
      })
      pendingSaves -= 1
      if (pendingSaves === 0) {
        set({ saveStatus: 'saved' })
      }
    } catch (error) {
      pendingSaves -= 1
      set({ saveStatus: 'error' })
      throw error
    }
  }

  function diagramContext(diagram: Diagram): Partial<AppState> {
    return {
      activeDiagram: diagram,
      semanticMetadata: (diagram.semantic_metadata as Record<string, ShapeMetadata> | null) ?? {},
      validationResults: [],
      activeElementId: null,
      saveStatus: 'idle',
    }
  }

  return {
    workspaces: [],
    activeWorkspace: null,
    projects: [],
    activeProject: null,
    folders: [],
    diagrams: [],
    activeDiagram: null,
    isLoadingWorkspaces: true,
    isLoadingProject: false,
    isLoadingDiagram: false,
    saveStatus: 'idle',
    documentation: null,
    editor: null,
    isSidebarOpen: true,
    isInspectorOpen: false,
    inspectorTab: 'properties',
    isCommandPaletteOpen: false,
    isValidationOpen: false,
    newDiagramDialog: null,
    comments: [],
    activeElementId: null,
    isPresentationMode: false,
    semanticMetadata: {},
    validationResults: [],
    presence: EMPTY_PRESENCE,
    members: [],
    myRole: null,

    loadWorkspaces: async () => {
      set({ isLoadingWorkspaces: true })
      try {
        const workspaces = await listWorkspaces()
        set({ workspaces })
        if (get().activeWorkspace !== null || workspaces.length === 0) {
          return
        }
        const lastId = recall(LAST_WORKSPACE_KEY)
        const workspace = workspaces.find((item) => item.id === lastId) ?? workspaces[0]
        await get().setActiveWorkspace(workspace)
      } finally {
        set({ isLoadingWorkspaces: false })
      }
    },

    setActiveWorkspace: async (workspace) => {
      remember(LAST_WORKSPACE_KEY, workspace.id)
      set({
        activeWorkspace: workspace,
        projects: [],
        activeProject: null,
        folders: [],
        diagrams: [],
        members: [],
        myRole: null,
      })
      void get().loadMembers(workspace.id)
      const projects = await listProjects(workspace.id)
      if (get().activeWorkspace?.id !== workspace.id) {
        return
      }
      set({ projects })
      if (get().activeProject !== null || projects.length === 0) {
        return
      }
      const lastId = recall(LAST_PROJECT_KEY)
      const project = projects.find((item) => item.id === lastId) ?? projects[0]
      await get().setActiveProject(project)
    },

    setActiveProject: async (project) => {
      remember(LAST_PROJECT_KEY, project.id)
      // Clear the previous project's tree immediately; otherwise the newly
      // expanded project shows the last project's folders/diagrams until the
      // async fetch resolves, which looks like the tree is caching stale state.
      const isSameProject = get().activeProject?.id === project.id
      set({
        activeProject: project,
        isLoadingProject: true,
        ...(isSameProject ? {} : { folders: [], diagrams: [] }),
      })
      try {
        const [folders, diagrams] = await Promise.all([
          listFolders(project.id),
          listDiagrams(project.id),
        ])
        if (get().activeProject?.id === project.id) {
          set({ folders, diagrams })
        }
      } finally {
        set({ isLoadingProject: false })
      }
    },

    setActiveDiagram: async (diagram) => {
      set({ ...diagramContext(diagram), documentation: null, comments: [] })
      const [documentation, comments] = await Promise.all([getDocumentation(diagram.id), listComments(diagram.id)])
      if (get().activeDiagram?.id === diagram.id) {
        set({ documentation, comments })
      }
    },

    closeDiagram: () => {
      if (get().isPresentationMode) {
        get().exitPresentation()
      }
      set({
        activeDiagram: null,
        documentation: null,
        comments: [],
        semanticMetadata: {},
        validationResults: [],
        activeElementId: null,
        presence: EMPTY_PRESENCE,
        saveStatus: 'idle',
      })
    },

    loadDiagram: async (diagramId) => {
      const current = get().activeDiagram
      if (current !== null && current.id === diagramId) {
        return
      }

      const known = get().diagrams.find((diagram) => diagram.id === diagramId)
      if (known !== undefined) {
        await get().setActiveDiagram(known)
        return
      }

      // Direct navigation / refresh: we only have the diagram id, so scan the
      // workspaces until we find its project, then hydrate the full context.
      set({ isLoadingDiagram: true })
      try {
        let workspaces = get().workspaces
        if (workspaces.length === 0) {
          workspaces = await listWorkspaces()
          set({ workspaces })
        }

        for (const workspace of workspaces) {
          const projects = await listProjects(workspace.id)
          for (const project of projects) {
            const diagrams = await listDiagrams(project.id)
            const found = diagrams.find((diagram) => diagram.id === diagramId)
            if (found === undefined) {
              continue
            }
            const [folders, documentation, comments] = await Promise.all([
              listFolders(project.id),
              getDocumentation(found.id),
              listComments(found.id),
            ])
            remember(LAST_WORKSPACE_KEY, workspace.id)
            remember(LAST_PROJECT_KEY, project.id)
            set({
              activeWorkspace: workspace,
              projects,
              activeProject: project,
              folders,
              diagrams,
              documentation,
              comments,
              ...diagramContext(found),
            })
            void get().loadMembers(workspace.id)
            return
          }
        }
      } finally {
        set({ isLoadingDiagram: false })
      }
    },

    createWorkspace: async (name, slug) => {
      const workspace = await apiCreateWorkspace(name, slug)
      set({ workspaces: [...get().workspaces, workspace] })
      await get().setActiveWorkspace(workspace)
    },

    createProject: async (name) => {
      const { activeWorkspace } = get()
      if (activeWorkspace === null) {
        return null
      }
      const project = await apiCreateProject(activeWorkspace.id, name)
      set({ projects: [...get().projects, project] })
      await get().setActiveProject(project)
      return project
    },

    renameProject: async (project, name) => {
      const updated = await apiUpdateProject(project.workspace_id, project.id, name, project.description ?? '')
      set({
        projects: get().projects.map((item) => (item.id === updated.id ? updated : item)),
        activeProject: get().activeProject?.id === updated.id ? updated : get().activeProject,
      })
    },

    deleteProject: async (project) => {
      await apiDeleteProject(project.workspace_id, project.id)
      const projects = get().projects.filter((item) => item.id !== project.id)
      set({ projects })
      if (get().activeDiagram?.project_id === project.id) {
        get().closeDiagram()
      }
      if (get().activeProject?.id !== project.id) {
        return
      }
      set({ activeProject: null, folders: [], diagrams: [] })
      remember(LAST_PROJECT_KEY, null)
      if (projects.length > 0) {
        await get().setActiveProject(projects[0])
      }
    },

    createFolder: async (name, parentId) => {
      const { activeProject } = get()
      if (activeProject === null) {
        return
      }
      const folder = await apiCreateFolder(activeProject.id, name, parentId)
      set({ folders: [...get().folders, folder] })
    },

    renameFolder: async (folder, name) => {
      const updated = await apiUpdateFolder(folder.project_id, folder.id, name, folder.parent_folder_id)
      set({ folders: get().folders.map((item) => (item.id === updated.id ? updated : item)) })
    },

    deleteFolder: async (folder) => {
      await apiDeleteFolder(folder.project_id, folder.id)
      // Children are re-parented server side, so reload the tree instead of guessing.
      const [folders, diagrams] = await Promise.all([
        listFolders(folder.project_id),
        listDiagrams(folder.project_id),
      ])
      set({ folders, diagrams })
    },

    createDiagram: async (name, folderId) => {
      const { activeProject } = get()
      if (activeProject === null) {
        return null
      }
      const diagram = await apiCreateDiagram(activeProject.id, name, folderId)
      set({ diagrams: [...get().diagrams, diagram] })
      return diagram
    },

    renameDiagram: async (name, diagram) => {
      await persistDiagram({ name }, diagram)
    },

    deleteDiagram: async (diagram) => {
      await apiDeleteDiagram(diagram.project_id, diagram.id)
      set({ diagrams: get().diagrams.filter((item) => item.id !== diagram.id) })
      if (get().activeDiagram?.id === diagram.id) {
        get().closeDiagram()
      }
    },

    saveCanvasState: async (state) => {
      await persistDiagram({ canvas_state: state })
    },

    applyPushedDiagram: (pushed) => {
      const current = get().activeDiagram
      if (current?.id !== pushed.id || isOlder(pushed.updated_at, current.updated_at)) {
        return false
      }
      // Panel edits still waiting for their debounced save survive unless someone else
      // actually changed the metadata.
      const metadataChanged =
        JSON.stringify(pushed.semantic_metadata ?? null) !== JSON.stringify(current.semantic_metadata ?? null)
      const updated = { ...current, ...pushed }
      set({
        activeDiagram: updated,
        diagrams: get().diagrams.map((item) => (item.id === updated.id ? updated : item)),
        ...(metadataChanged
          ? { semanticMetadata: (pushed.semantic_metadata as Record<string, ShapeMetadata> | null) ?? {} }
          : {}),
      })
      return true
    },

    saveDocumentation: async (content) => {
      const { activeDiagram } = get()
      if (activeDiagram === null) {
        return
      }
      set({ saveStatus: 'saving' })
      try {
        const documentation = await upsertDocumentation(activeDiagram.id, content)
        set({ documentation, saveStatus: 'saved' })
      } catch (error) {
        set({ saveStatus: 'error' })
        throw error
      }
    },

    setEditor: (editor) => set({ editor }),

    toggleSidebar: () => set({ isSidebarOpen: !get().isSidebarOpen }),

    toggleInspector: () => set({ isInspectorOpen: !get().isInspectorOpen }),

    openInspector: (tab) => set({ inspectorTab: tab, isInspectorOpen: true }),

    closeInspector: () => set({ isInspectorOpen: false }),

    setCommandPaletteOpen: (open) => set({ isCommandPaletteOpen: open }),

    openNewDiagram: (folderId) => set({ newDiagramDialog: { folderId } }),

    closeNewDiagram: () => set({ newDiagramDialog: null }),

    loadComments: async (diagramId) => {
      const comments = await listComments(diagramId)
      set({ comments })
    },

    addComment: async (elementId, content) => {
      const { activeDiagram } = get()
      if (activeDiagram === null) {
        return
      }
      const comment = await apiCreateComment(activeDiagram.id, elementId, content)
      set({ comments: [...get().comments, comment] })
    },

    setActiveElement: (id) => set({ activeElementId: id }),

    commentOnElement: (id) => set({ activeElementId: id, inspectorTab: 'comments', isInspectorOpen: true }),

    enterPresentation: () => {
      const element = document.documentElement
      if (element.requestFullscreen !== undefined) {
        void element.requestFullscreen().catch(() => undefined)
      }
      set({ isPresentationMode: true })
    },

    exitPresentation: () => {
      if (document.fullscreenElement !== null && document.exitFullscreen !== undefined) {
        void document.exitFullscreen().catch(() => undefined)
      }
      set({ isPresentationMode: false })
    },

    updateShapeMetadata: (shapeId, metadata) => {
      const current = get().semanticMetadata
      set({
        semanticMetadata: {
          ...current,
          [shapeId]: { ...current[shapeId], ...metadata },
        },
      })
    },

    saveSemanticMetadata: async () => {
      await persistDiagram({ semantic_metadata: get().semanticMetadata as SemanticMetadata })
    },

    runValidation: () => {
      const { editor, semanticMetadata } = get()
      if (editor === null) {
        set({ validationResults: [], isValidationOpen: true })
        return
      }
      const graph = buildArchitectureGraph(editor)
      set({ validationResults: validateArchitecture(graph, semanticMetadata), isValidationOpen: true })
    },

    closeValidation: () => set({ isValidationOpen: false }),

    setPresence: (presence) => set({ presence }),

    loadMembers: async (workspaceId) => {
      if (!authConfig.enabled) {
        set({ members: [], myRole: null })
        return
      }
      const members = await listMembers(workspaceId)
      if (get().activeWorkspace?.id !== workspaceId) {
        return
      }
      const email = useAuthStore.getState().profile?.email.toLowerCase()
      set({ members, myRole: members.find((member) => member.email === email)?.role ?? null })
    },

    addMember: async (email, role) => {
      const { activeWorkspace } = get()
      if (activeWorkspace === null) {
        return
      }
      const member = await apiAddMember(activeWorkspace.id, email, role)
      set({ members: [...get().members, member].sort((a, b) => a.name.localeCompare(b.name)) })
    },

    updateMemberRole: async (userId, role) => {
      const { activeWorkspace } = get()
      if (activeWorkspace === null) {
        return
      }
      await apiUpdateMemberRole(activeWorkspace.id, userId, role)
      await get().loadMembers(activeWorkspace.id)
    },

    removeMember: async (userId) => {
      const { activeWorkspace } = get()
      if (activeWorkspace === null) {
        return
      }
      const myEmail = useAuthStore.getState().profile?.email.toLowerCase()
      const isLeaving = get().members.some((member) => member.user_id === userId && member.email === myEmail)
      await apiRemoveMember(activeWorkspace.id, userId)
      if (!isLeaving) {
        await get().loadMembers(activeWorkspace.id)
        return
      }
      // Leaving drops access right away, so move to another workspace.
      get().closeDiagram()
      set({ activeWorkspace: null, projects: [], activeProject: null, folders: [], diagrams: [], members: [], myRole: null })
      await get().loadWorkspaces()
    },
  }
})
