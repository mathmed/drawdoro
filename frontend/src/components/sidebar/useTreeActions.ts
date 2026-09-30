import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import type { DiagramSummary, Folder, Project } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog, promptDialog } from '../../store/useDialogStore'

export interface TreeActions {
  createProject: () => Promise<void>
  renameProject: (project: Project) => Promise<void>
  deleteProject: (project: Project) => Promise<void>
  createFolder: (parentId?: string) => Promise<void>
  renameFolder: (folder: Folder) => Promise<void>
  deleteFolder: (folder: Folder) => Promise<void>
  newDiagram: (folderId?: string) => void
  renameDiagram: (diagram: DiagramSummary) => Promise<void>
  deleteDiagram: (diagram: DiagramSummary) => Promise<void>
}

// Everything the tree rows can do, with the confirmation and naming dialogs in front of it.
// Stable across renders so memoised rows do not re-render when the sidebar does.
export function useTreeActions(expandFolder: (id: string) => void): TreeActions {
  const navigate = useNavigate()
  return useMemo(() => buildActions(navigate, expandFolder), [navigate, expandFolder])
}

function buildActions(navigate: (path: string) => void, expandFolder: (id: string) => void): TreeActions {
  const store = useAppStore.getState

  return {
    createProject: async () => {
      const name = await promptDialog({
        title: 'New project',
        description: 'Projects hold the diagrams, docs and decisions for a system.',
        label: 'Name',
        placeholder: 'e.g. Payments platform',
      })
      if (name === null) {
        return
      }
      await store().createProject(name)
      navigate('/')
    },

    renameProject: async (project) => {
      const name = await promptDialog({
        title: 'Rename project',
        label: 'Name',
        initialValue: project.name,
        confirmLabel: 'Rename',
      })
      if (name !== null && name !== project.name) {
        await store().renameProject(project, name)
      }
    },

    deleteProject: async (project) => {
      const confirmed = await confirmDialog({
        title: `Delete “${project.name}”?`,
        description: 'All folders, diagrams, docs and comments in this project will be permanently deleted.',
        confirmLabel: 'Delete project',
        danger: true,
      })
      if (!confirmed) {
        return
      }
      await store().deleteProject(project)
      navigate('/')
    },

    createFolder: async (parentId) => {
      const name = await promptDialog({ title: 'New folder', label: 'Name', placeholder: 'e.g. Services' })
      if (name === null) {
        return
      }
      await store().createFolder(name, parentId)
      if (parentId !== undefined) {
        expandFolder(parentId)
      }
    },

    renameFolder: async (folder) => {
      const name = await promptDialog({
        title: 'Rename folder',
        label: 'Name',
        initialValue: folder.name,
        confirmLabel: 'Rename',
      })
      if (name !== null && name !== folder.name) {
        await store().renameFolder(folder, name)
      }
    },

    deleteFolder: async (folder) => {
      const confirmed = await confirmDialog({
        title: `Delete folder “${folder.name}”?`,
        description: 'The folder is removed. Diagrams and subfolders inside it move to the project root.',
        confirmLabel: 'Delete folder',
        danger: true,
      })
      if (confirmed) {
        await store().deleteFolder(folder)
      }
    },

    newDiagram: (folderId) => {
      if (folderId !== undefined) {
        expandFolder(folderId)
      }
      store().openNewDiagram(folderId)
    },

    renameDiagram: async (diagram) => {
      const name = await promptDialog({
        title: 'Rename diagram',
        label: 'Name',
        initialValue: diagram.name,
        confirmLabel: 'Rename',
      })
      if (name !== null && name !== diagram.name) {
        await store().renameDiagram(name, diagram)
      }
    },

    deleteDiagram: async (diagram) => {
      const confirmed = await confirmDialog({
        title: `Delete “${diagram.name}”?`,
        description: 'The diagram, its documentation and comments will be permanently deleted.',
        confirmLabel: 'Delete diagram',
        danger: true,
      })
      if (!confirmed) {
        return
      }
      const wasActive = store().activeDiagram?.id === diagram.id
      await store().deleteDiagram(diagram)
      if (wasActive) {
        navigate('/')
      }
    },
  }
}
