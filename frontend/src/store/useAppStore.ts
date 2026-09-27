import type { Editor } from 'tldraw'
import { create } from 'zustand'

import {
  createAdr as apiCreateAdr,
  deleteAdr as apiDeleteAdr,
  listAdrs,
  updateAdr as apiUpdateAdr,
} from '../api/adrs'
import { createComment as apiCreateComment, listComments } from '../api/comments'
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
  Adr,
  AdrStatus,
  CanvasState,
  Comment,
  CreateAdrData,
  Diagram,
  DocumentationPage,
  Folder,
  Project,
  SemanticMetadata,
  ShapeMetadata,
  ValidationResult,
  Workspace,
} from '../api/types'
import { buildArchitectureGraph, validateArchitecture } from '../utils/validateArchitecture'

type RightPanelTab = 'docs' | 'adrs' | 'info'

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
  comments: Comment[]
  activeElementId: string | null
  isCommentsPanelOpen: boolean
  adrs: Adr[]
  rightPanelTab: RightPanelTab
  isPresentationMode: boolean
  semanticMetadata: Record<string, ShapeMetadata>
  validationResults: ValidationResult[]

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
  loadComments: (diagramId: string) => Promise<void>
  addComment: (elementId: string, content: string) => Promise<void>
  toggleCommentsPanel: () => void
  setActiveElement: (id: string | null) => void
  loadAdrs: (diagramId: string) => Promise<void>
  createAdr: (data: CreateAdrData) => Promise<void>
  updateAdr: (adrId: string, data: CreateAdrData) => Promise<void>
  updateAdrStatus: (adrId: string, status: AdrStatus) => Promise<void>
  deleteAdr: (adrId: string) => Promise<void>
  setRightPanelTab: (tab: RightPanelTab) => void
  enterPresentation: () => void
  exitPresentation: () => void
  updateShapeMetadata: (shapeId: string, metadata: Partial<ShapeMetadata>) => void
  saveSemanticMetadata: () => Promise<void>
  runValidation: () => void
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
  comments: [],
  activeElementId: null,
  isCommentsPanelOpen: false,
  adrs: [],
  rightPanelTab: 'docs',
  isPresentationMode: false,
  semanticMetadata: {},
  validationResults: [],

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
    set({
      activeDiagram: diagram,
      semanticMetadata: (diagram.semantic_metadata as Record<string, ShapeMetadata> | null) ?? {},
      validationResults: [],
      activeElementId: null,
    })
    const [documentation, adrs, comments] = await Promise.all([
      getDocumentation(diagram.id),
      listAdrs(diagram.id),
      listComments(diagram.id),
    ])
    set({ documentation, adrs, comments })
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
          const [folders, documentation, adrs, comments] = await Promise.all([
            listFolders(project.id),
            getDocumentation(found.id),
            listAdrs(found.id),
            listComments(found.id),
          ])
          set({
            activeWorkspace: workspace,
            projects,
            activeProject: project,
            folders,
            diagrams,
            activeDiagram: found,
            documentation,
            adrs,
            comments,
            semanticMetadata:
              (found.semantic_metadata as Record<string, ShapeMetadata> | null) ?? {},
            validationResults: [],
            activeElementId: null,
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

  toggleCommentsPanel: () => set({ isCommentsPanelOpen: !get().isCommentsPanelOpen }),

  setActiveElement: (id) => set({ activeElementId: id }),

  loadAdrs: async (diagramId) => {
    const adrs = await listAdrs(diagramId)
    set({ adrs })
  },

  createAdr: async (data) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const adr = await apiCreateAdr(activeDiagram.id, data)
    set({ adrs: [...get().adrs, adr] })
  },

  updateAdr: async (adrId, data) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    const updated = await apiUpdateAdr(activeDiagram.id, adrId, data)
    set({ adrs: get().adrs.map((adr) => (adr.id === adrId ? updated : adr)) })
  },

  updateAdrStatus: async (adrId, status) => {
    const { activeDiagram, adrs } = get()
    const current = adrs.find((adr) => adr.id === adrId)
    if (activeDiagram === null || current === undefined) {
      return
    }
    const updated = await apiUpdateAdr(activeDiagram.id, adrId, {
      title: current.title,
      context: current.context,
      decision: current.decision,
      consequences: current.consequences,
      status,
    })
    set({ adrs: get().adrs.map((adr) => (adr.id === adrId ? updated : adr)) })
  },

  deleteAdr: async (adrId) => {
    const { activeDiagram } = get()
    if (activeDiagram === null) {
      return
    }
    await apiDeleteAdr(activeDiagram.id, adrId)
    set({ adrs: get().adrs.filter((adr) => adr.id !== adrId) })
  },

  setRightPanelTab: (tab) => set({ rightPanelTab: tab, isDocsPanelOpen: true }),

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
    const { activeDiagram, semanticMetadata } = get()
    if (activeDiagram === null) {
      return
    }
    const updated = await updateDiagram(activeDiagram.project_id, activeDiagram.id, {
      name: activeDiagram.name,
      folder_id: activeDiagram.folder_id,
      canvas_state: activeDiagram.canvas_state,
      mermaid_source: activeDiagram.mermaid_source,
      d2_source: activeDiagram.d2_source,
      semantic_metadata: semanticMetadata as SemanticMetadata,
    })
    set({
      activeDiagram: updated,
      diagrams: get().diagrams.map((diagram) =>
        diagram.id === updated.id ? updated : diagram,
      ),
    })
  },

  runValidation: () => {
    const { editor, semanticMetadata } = get()
    if (editor === null) {
      set({ validationResults: [] })
      return
    }
    const graph = buildArchitectureGraph(editor)
    set({ validationResults: validateArchitecture(graph, semanticMetadata) })
  },
}))
