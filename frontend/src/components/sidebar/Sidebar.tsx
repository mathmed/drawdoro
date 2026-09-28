import {
  ChevronRight,
  ChevronsUpDown,
  FilePlus2,
  Folder as FolderIcon,
  FolderOpen,
  FolderPlus,
  House,
  Layers,
  Monitor,
  Moon,
  MoreHorizontal,
  PanelLeftClose,
  Pencil,
  Plus,
  Search,
  Sun,
  Trash2,
  Workflow,
} from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import type { Diagram, Folder, Project } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog, promptDialog } from '../../store/useDialogStore'
import { useThemeStore, type ThemePreference } from '../../store/useThemeStore'
import { initial, modKey, slugify } from '../../utils/format'
import Logo from '../ui/Logo'
import Menu, { type MenuEntry } from '../ui/Menu'

const INDENT = 14

function RowMenu({ items, label }: { items: MenuEntry[]; label: string }) {
  return (
    <Menu
      align="end"
      items={items}
      trigger={({ toggle }) => (
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-xs"
          aria-label={label}
          onClick={(event) => {
            event.stopPropagation()
            toggle()
          }}
        >
          {label === 'Add' ? <Plus size={14} /> : <MoreHorizontal size={14} />}
        </button>
      )}
    />
  )
}

const THEME_OPTIONS: { value: ThemePreference; icon: ReactNode; label: string }[] = [
  { value: 'light', icon: <Sun size={14} />, label: 'Light' },
  { value: 'dark', icon: <Moon size={14} />, label: 'Dark' },
  { value: 'system', icon: <Monitor size={14} />, label: 'System' },
]

export default function Sidebar() {
  const navigate = useNavigate()

  const workspaces = useAppStore((state) => state.workspaces)
  const activeWorkspace = useAppStore((state) => state.activeWorkspace)
  const projects = useAppStore((state) => state.projects)
  const activeProject = useAppStore((state) => state.activeProject)
  const folders = useAppStore((state) => state.folders)
  const diagrams = useAppStore((state) => state.diagrams)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isLoadingProject = useAppStore((state) => state.isLoadingProject)

  const setActiveWorkspace = useAppStore((state) => state.setActiveWorkspace)
  const setActiveProject = useAppStore((state) => state.setActiveProject)
  const createWorkspace = useAppStore((state) => state.createWorkspace)
  const createProject = useAppStore((state) => state.createProject)
  const renameProject = useAppStore((state) => state.renameProject)
  const deleteProject = useAppStore((state) => state.deleteProject)
  const createFolder = useAppStore((state) => state.createFolder)
  const renameFolder = useAppStore((state) => state.renameFolder)
  const deleteFolder = useAppStore((state) => state.deleteFolder)
  const renameDiagram = useAppStore((state) => state.renameDiagram)
  const deleteDiagram = useAppStore((state) => state.deleteDiagram)
  const openNewDiagram = useAppStore((state) => state.openNewDiagram)
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)
  const setCommandPaletteOpen = useAppStore((state) => state.setCommandPaletteOpen)

  const themePreference = useThemeStore((state) => state.preference)
  const setThemePreference = useThemeStore((state) => state.setPreference)

  const [collapsedProject, setCollapsedProject] = useState<string | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // Reveal the active diagram in the tree by expanding every folder above it.
  useEffect(() => {
    if (activeDiagram === null || activeDiagram.folder_id === null) {
      return
    }
    const ancestors: string[] = []
    let current = folders.find((folder) => folder.id === activeDiagram.folder_id)
    while (current !== undefined) {
      ancestors.push(current.id)
      const parentId = current.parent_folder_id
      current = folders.find((folder) => folder.id === parentId)
    }
    setExpandedFolders((previous) => new Set([...previous, ...ancestors]))
  }, [activeDiagram, folders])

  function toggleFolder(id: string): void {
    setExpandedFolders((current) => {
      const next = new Set(current)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  async function handleCreateWorkspace(): Promise<void> {
    const name = await promptDialog({
      title: 'New workspace',
      description: 'Workspaces group projects and the people who work on them.',
      label: 'Name',
      placeholder: 'e.g. Platform Engineering',
    })
    if (name === null) {
      return
    }
    const slug = slugify(name) || `workspace-${Date.now()}`
    await createWorkspace(name, slug)
  }

  async function handleCreateProject(): Promise<void> {
    const name = await promptDialog({
      title: 'New project',
      description: 'Projects hold the diagrams, docs and decisions for a system.',
      label: 'Name',
      placeholder: 'e.g. Payments platform',
    })
    if (name !== null) {
      await createProject(name)
      navigate('/')
    }
  }

  async function handleCreateFolder(parentId?: string): Promise<void> {
    const name = await promptDialog({ title: 'New folder', label: 'Name', placeholder: 'e.g. Services' })
    if (name === null) {
      return
    }
    await createFolder(name, parentId)
    if (parentId !== undefined) {
      setExpandedFolders((current) => new Set([...current, parentId]))
    }
  }

  function handleNewDiagram(folderId?: string): void {
    if (folderId !== undefined) {
      setExpandedFolders((current) => new Set([...current, folderId]))
    }
    openNewDiagram(folderId)
  }

  async function handleSelectProject(project: Project): Promise<void> {
    if (activeProject?.id === project.id) {
      setCollapsedProject((current) => (current === project.id ? null : project.id))
      return
    }
    setCollapsedProject(null)
    await setActiveProject(project)
    if (activeDiagram !== null) {
      navigate('/')
    }
  }

  async function handleRenameProject(project: Project): Promise<void> {
    const name = await promptDialog({
      title: 'Rename project',
      label: 'Name',
      initialValue: project.name,
      confirmLabel: 'Rename',
    })
    if (name !== null && name !== project.name) {
      await renameProject(project, name)
    }
  }

  async function handleDeleteProject(project: Project): Promise<void> {
    const confirmed = await confirmDialog({
      title: `Delete “${project.name}”?`,
      description: 'All folders, diagrams, docs and comments in this project will be permanently deleted.',
      confirmLabel: 'Delete project',
      danger: true,
    })
    if (confirmed) {
      await deleteProject(project)
      navigate('/')
    }
  }

  async function handleRenameFolder(folder: Folder): Promise<void> {
    const name = await promptDialog({
      title: 'Rename folder',
      label: 'Name',
      initialValue: folder.name,
      confirmLabel: 'Rename',
    })
    if (name !== null && name !== folder.name) {
      await renameFolder(folder, name)
    }
  }

  async function handleDeleteFolder(folder: Folder): Promise<void> {
    const confirmed = await confirmDialog({
      title: `Delete folder “${folder.name}”?`,
      description: 'The folder is removed. Diagrams and subfolders inside it move to the project root.',
      confirmLabel: 'Delete folder',
      danger: true,
    })
    if (confirmed) {
      await deleteFolder(folder)
    }
  }

  async function handleRenameDiagram(diagram: Diagram): Promise<void> {
    const name = await promptDialog({
      title: 'Rename diagram',
      label: 'Name',
      initialValue: diagram.name,
      confirmLabel: 'Rename',
    })
    if (name !== null && name !== diagram.name) {
      await renameDiagram(name, diagram)
    }
  }

  async function handleDeleteDiagram(diagram: Diagram): Promise<void> {
    const confirmed = await confirmDialog({
      title: `Delete “${diagram.name}”?`,
      description: 'The diagram, its documentation and comments will be permanently deleted.',
      confirmLabel: 'Delete diagram',
      danger: true,
    })
    if (!confirmed) {
      return
    }
    const wasActive = activeDiagram?.id === diagram.id
    await deleteDiagram(diagram)
    if (wasActive) {
      navigate('/')
    }
  }

  function childFolders(parentId: string | null): Folder[] {
    return folders
      .filter((folder) => folder.parent_folder_id === parentId)
      .sort((a, b) => a.name.localeCompare(b.name))
  }

  function folderDiagrams(folderId: string | null): Diagram[] {
    return diagrams
      .filter((diagram) => diagram.folder_id === folderId)
      .sort((a, b) => a.name.localeCompare(b.name))
  }

  function addMenu(folderId?: string): MenuEntry[] {
    return [
      { label: 'New diagram', icon: <FilePlus2 size={15} />, onSelect: () => handleNewDiagram(folderId) },
      { label: 'New folder', icon: <FolderPlus size={15} />, onSelect: () => void handleCreateFolder(folderId) },
    ]
  }

  function renderDiagram(diagram: Diagram, depth: number): ReactNode {
    return (
      <div
        key={diagram.id}
        className="tree-row"
        data-active={activeDiagram?.id === diagram.id}
        style={{ paddingLeft: 8 + depth * INDENT + 18 }}
        onClick={() => navigate(`/diagrams/${diagram.id}`)}
      >
        <Workflow size={15} />
        <span className="tree-label">{diagram.name}</span>
        <div className="tree-actions">
          <RowMenu
            label="More"
            items={[
              { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void handleRenameDiagram(diagram) },
              { kind: 'separator' },
              {
                label: 'Delete',
                icon: <Trash2 size={15} />,
                danger: true,
                onSelect: () => void handleDeleteDiagram(diagram),
              },
            ]}
          />
        </div>
      </div>
    )
  }

  function renderFolder(folder: Folder, depth: number): ReactNode {
    const isExpanded = expandedFolders.has(folder.id)
    return (
      <div key={folder.id}>
        <div
          className="tree-row"
          style={{ paddingLeft: 8 + depth * INDENT }}
          onClick={() => toggleFolder(folder.id)}
        >
          <span className="tree-chevron" data-open={isExpanded}>
            <ChevronRight size={14} />
          </span>
          {isExpanded ? <FolderOpen size={15} /> : <FolderIcon size={15} />}
          <span className="tree-label">{folder.name}</span>
          <div className="tree-actions">
            <RowMenu label="Add" items={addMenu(folder.id)} />
            <RowMenu
              label="More"
              items={[
                { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void handleRenameFolder(folder) },
                { kind: 'separator' },
                {
                  label: 'Delete',
                  icon: <Trash2 size={15} />,
                  danger: true,
                  onSelect: () => void handleDeleteFolder(folder),
                },
              ]}
            />
          </div>
        </div>
        {isExpanded ? (
          <div>
            {childFolders(folder.id).map((child) => renderFolder(child, depth + 1))}
            {folderDiagrams(folder.id).map((diagram) => renderDiagram(diagram, depth + 1))}
            {childFolders(folder.id).length === 0 && folderDiagrams(folder.id).length === 0 ? (
              <div className="tree-empty" style={{ paddingLeft: 8 + (depth + 1) * INDENT + 18 }}>
                Empty folder
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    )
  }

  function renderProject(project: Project): ReactNode {
    const isActive = activeProject?.id === project.id
    const isExpanded = isActive && collapsedProject !== project.id
    const isEmpty = folders.length === 0 && diagrams.length === 0
    return (
      <div key={project.id}>
        <div
          className="tree-row"
          data-strong={isActive}
          style={{ paddingLeft: 8 }}
          onClick={() => void handleSelectProject(project)}
        >
          <span className="tree-chevron" data-open={isExpanded}>
            <ChevronRight size={14} />
          </span>
          <Layers size={15} />
          <span className="tree-label">{project.name}</span>
          <div className="tree-actions">
            {isActive ? <RowMenu label="Add" items={addMenu()} /> : null}
            <RowMenu
              label="More"
              items={[
                { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void handleRenameProject(project) },
                { kind: 'separator' },
                {
                  label: 'Delete project',
                  icon: <Trash2 size={15} />,
                  danger: true,
                  onSelect: () => void handleDeleteProject(project),
                },
              ]}
            />
          </div>
        </div>
        {isExpanded ? (
          <div>
            {childFolders(null).map((folder) => renderFolder(folder, 1))}
            {folderDiagrams(null).map((diagram) => renderDiagram(diagram, 1))}
            {isEmpty && !isLoadingProject ? (
              <div className="tree-empty" style={{ paddingLeft: 8 + INDENT + 18 }}>
                No diagrams yet ·{' '}
                <button type="button" onClick={() => handleNewDiagram()}>
                  Create one
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    )
  }

  const workspaceItems: MenuEntry[] = [
    { kind: 'label', label: 'Workspaces' },
    ...workspaces.map((workspace) => ({
      label: workspace.name,
      icon: <span className="avatar" style={{ width: 20, height: 20, fontSize: 10.5 }}>{initial(workspace.name)}</span>,
      checked: workspace.id === activeWorkspace?.id,
      onSelect: () => {
        void setActiveWorkspace(workspace)
        navigate('/')
      },
    })),
    { kind: 'separator' },
    { label: 'New workspace', icon: <Plus size={15} />, onSelect: () => void handleCreateWorkspace() },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Menu
          className="menu-anchor workspace-anchor"
          items={workspaceItems}
          trigger={({ toggle }) => (
            <button type="button" className="workspace-switcher" onClick={toggle}>
              <span className="avatar">{initial(activeWorkspace?.name)}</span>
              <span className="workspace-switcher-name">{activeWorkspace?.name ?? 'No workspace'}</span>
              <ChevronsUpDown size={14} />
            </button>
          )}
        />
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          aria-label="Collapse sidebar"
          data-tooltip={`Collapse  ${modKey} \\`}
          onClick={toggleSidebar}
        >
          <PanelLeftClose size={16} />
        </button>
      </div>

      <button type="button" className="sidebar-search" onClick={() => setCommandPaletteOpen(true)}>
        <Search size={14} />
        <span>Search…</span>
        <kbd className="kbd">{modKey} K</kbd>
      </button>

      <div className="sidebar-body scroll">
        <div
          className="tree-row"
          data-active={activeDiagram === null && activeProject !== null}
          style={{ paddingLeft: 8 }}
          onClick={() => navigate('/')}
        >
          <House size={15} />
          <span className="tree-label">Overview</span>
        </div>

        <div className="sidebar-section">
          <span>Projects</span>
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-xs"
            aria-label="New project"
            data-tooltip="New project"
            disabled={activeWorkspace === null}
            onClick={() => void handleCreateProject()}
          >
            <Plus size={14} />
          </button>
        </div>
        {projects.map((project) => renderProject(project))}
        {activeWorkspace !== null && projects.length === 0 ? (
          <div className="tree-empty">
            No projects ·{' '}
            <button type="button" onClick={() => void handleCreateProject()}>
              Create one
            </button>
          </div>
        ) : null}
      </div>

      <div className="sidebar-footer">
        <Logo size={20} withWordmark />
        <div className="segmented" role="group" aria-label="Theme">
          {THEME_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              aria-label={option.label}
              aria-pressed={themePreference === option.value}
              title={option.label}
              onClick={() => setThemePreference(option.value)}
            >
              {option.icon}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
