import type { Editor } from 'tldraw'
import { create } from 'zustand'

import { getDocumentation, upsertDocumentation } from '../api/documentation'
import {
  createDiagram as apiCreateDiagram,
  listDiagrams,
  updateDiagram,
} from '../api/diagrams'
import { createFolder as apiCreateFolder, listFolders } from '../api/folders'
import { createProject as apiCreateProject, listProjects } from '../api/projects'
import { createWorkspace as apiCreateWorkspace, listWorkspaces } from '../api/workspaces'
import type {
  CanvasState,
  Diagram,
  DocumentationPage,
  Folder,
  Project,
  Workspace,
} from '../api/types'

interface AppState {
  workspaces: Workspace[]
  activeWorkspace: Workspace | null
  projects: Project[]
  activeProject: Project | null
  folders: Folder[]
  diagrams: Diagram[]
  activeDiagram: Diagram | null
  documentation: DocumentationPage | null
  isDocsPanelOpen: boolean
  editor: Editor | null
  isCodePanelOpen: boolean
  isTemplateModalOpen: boolean
  codeLanguage: 'mermaid' | 'd2'

  loadWorkspaces: () => Promise<void>
  setActiveWorkspace: (workspace: Workspace) => Promise<void>
  setActiveProject: (project: Project) => Promise<void>
  setActiveDiagram: (diagram: Diagram) => Promise<void>
  loadDiagram: (diagramId: string) => Promise<void>
  createWorkspace: (name: string, slug: string) => Promise<void>
  createProject: (name: string) => Promise<void>
  createFolder: (name: string, parentId?: string) => Promise<void>
  createDiagram: (name: string, folderId?: string) => Promise<Diagram | null>
  saveCanvasState: (state: CanvasState) => Promise<void>
  saveDocumentation: (content: string) => Promise<void>
  renameDiagram: (name: string) => Promise<void>
  toggleDocsPanel: () => void
  setEditor: (editor: Editor | null) => void
  toggleCodePanel: () => void
  toggleTemplateModal: () => void
  setCodeLanguage: (lang: 'mermaid' | 'd2') => void
  saveMermaidSource: (source: string) => Promise<void>
  saveD2Source: (source: string) => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  workspaces: [],
  activeWorkspace: null,
  projects: [],
  activeProject: null,
  folders: [],
  diagrams: [],
  activeDiagram: null,
  documentation: null,
  isDocsPanelOpen: false,
  editor: null,
  isCodePanelOpen: false,
  isTemplateModalOpen: false,
  codeLanguage: 'mermaid',

  loadWorkspaces: async () => {
    const workspaces = await listWorkspaces()
    set({ workspaces })
    const { activeWorkspace } = get()
    if (activeWorkspace === null && workspaces.length > 0) {
      await get().setActiveWorkspace(workspaces[0])
    }
  },

  setActiveWorkspace: async (workspace) => {
    set({
      activeWorkspace: workspace,
      activeProject: null,
      folders: [],
      diagrams: [],
    })
    const projects = await listProjects(workspace.id)
    set({ projects })
  },

  setActiveProject: async (project) => {
    set({ activeProject: project })
    const [folders, diagrams] = await Promise.all([
      listFolders(project.id),
      listDiagrams(project.id),
    ])
    set({ folders, diagrams })
  },

  setActiveDiagram: async (diagram) => {
    set({ activeDiagram: diagram })
    const documentation = await getDocumentation(diagram.id)
    set({ documentation })
  },

  loadDiagram: async (diagramId) => {
    const current = get().activeDiagram
    if (current !== null && current.id === diagramId) {
      return
    }

    // Direct navigation / refresh: we only have the diagram id, so scan the
    // workspaces until we find its project, then hydrate the full context.
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
        if (found !== undefined) {
          const [folders, documentation] = await Promise.all([
            listFolders(project.id),
            getDocumentation(found.id),
          ])
          set({
            activeWorkspace: workspace,
            projects,
            activeProject: project,
            folders,
            diagrams,
            activeDiagram: found,
            documentation,
          })
          return
        }
      }
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
      return
    }
    const project = await apiCreateProject(activeWorkspace.id, name)
    set({ projects: [...get().projects, project] })
    await get().setActiveProject(project)
  },

  createFolder: async (name, parentId) => {
    const { activeProject } = get()
    if (activeProject === null) {
      return
    }
    const folder = await apiCreateFolder(activeProject.id, name, parentId)
    set({ folders: [...get().folders, folder] })
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

  saveCanvasState: async (state) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const updated = await updateDiagram(activeDiagram.project_id, activeDiagram.id, {
      name: activeDiagram.name,
      folder_id: activeDiagram.folder_id,
      canvas_state: state,
      mermaid_source: activeDiagram.mermaid_source,
      d2_source: activeDiagram.d2_source,
      semantic_metadata: activeDiagram.semantic_metadata ?? null,
    })
    set({
      activeDiagram: updated,
      diagrams: get().diagrams.map((diagram) =>
        diagram.id === updated.id ? updated : diagram,
      ),
    })
  },

  renameDiagram: async (name) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const updated = await updateDiagram(activeDiagram.project_id, activeDiagram.id, {
      name,
      folder_id: activeDiagram.folder_id,
      canvas_state: activeDiagram.canvas_state,
      mermaid_source: activeDiagram.mermaid_source,
      d2_source: activeDiagram.d2_source,
      semantic_metadata: activeDiagram.semantic_metadata ?? null,
    })
    set({
      activeDiagram: updated,
      diagrams: get().diagrams.map((diagram) =>
        diagram.id === updated.id ? updated : diagram,
      ),
    })
  },

  saveDocumentation: async (content) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const documentation = await upsertDocumentation(activeDiagram.id, content)
    set({ documentation })
  },

  toggleDocsPanel: () => set({ isDocsPanelOpen: !get().isDocsPanelOpen }),

  setEditor: (editor) => set({ editor }),

  toggleCodePanel: () => set({ isCodePanelOpen: !get().isCodePanelOpen }),

  toggleTemplateModal: () => set({ isTemplateModalOpen: !get().isTemplateModalOpen }),

  setCodeLanguage: (lang) => set({ codeLanguage: lang }),

  saveMermaidSource: async (source) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const updated = await updateDiagram(activeDiagram.project_id, activeDiagram.id, {
      name: activeDiagram.name,
      folder_id: activeDiagram.folder_id,
      canvas_state: activeDiagram.canvas_state,
      mermaid_source: source,
      d2_source: activeDiagram.d2_source,
      semantic_metadata: activeDiagram.semantic_metadata ?? null,
    })
    set({
      activeDiagram: updated,
      diagrams: get().diagrams.map((diagram) =>
        diagram.id === updated.id ? updated : diagram,
      ),
    })
  },

  saveD2Source: async (source) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const updated = await updateDiagram(activeDiagram.project_id, activeDiagram.id, {
      name: activeDiagram.name,
      folder_id: activeDiagram.folder_id,
      canvas_state: activeDiagram.canvas_state,
      mermaid_source: activeDiagram.mermaid_source,
      d2_source: source,
      semantic_metadata: activeDiagram.semantic_metadata ?? null,
    })
    set({
      activeDiagram: updated,
      diagrams: get().diagrams.map((diagram) =>
        diagram.id === updated.id ? updated : diagram,
      ),
    })
  },
}))
