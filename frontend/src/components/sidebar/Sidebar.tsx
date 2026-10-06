import { House, PanelLeftClose, Plus, Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { Folder, Project } from '../../api/types'
import { useWorkspacePresence } from '../../hooks/useWorkspacePresence'
import { useAppStore } from '../../store/useAppStore'
import { modKey } from '../../utils/format'
import LoadingGate from '../ui/loading/LoadingGate'
import type { TreeViewProps } from './FolderNode'
import ProjectNode from './ProjectNode'
import SidebarFooter from './SidebarFooter'
import { ProjectListSkeleton } from './TreeSkeleton'
import { buildTreeIndex, folderAncestors } from './treeIndex'
import { useTreeActions } from './useTreeActions'
import WorkspaceSwitcher from './WorkspaceSwitcher'

// The tree position whose folders were last revealed: a new one expands its ancestors again.
interface RevealedFor {
  activeDiagramId: string | null
  activeFolderId: string | null
  folders: Folder[]
}

export default function Sidebar() {
  const navigate = useNavigate()

  const activeWorkspace = useAppStore((state) => state.activeWorkspace)
  const projects = useAppStore((state) => state.projects)
  const activeProject = useAppStore((state) => state.activeProject)
  const folders = useAppStore((state) => state.folders)
  const diagrams = useAppStore((state) => state.diagrams)
  // Primitives rather than the diagram itself: it changes on every save of the canvas.
  const activeDiagramId = useAppStore((state) => state.activeDiagram?.id ?? null)
  const activeFolderId = useAppStore((state) => state.activeDiagram?.folder_id ?? null)
  const isLoadingProject = useAppStore((state) => state.isLoadingProject)
  const isLoadingProjectList = useAppStore(
    (state) =>
      state.projects.length === 0 &&
      (state.isLoadingProjects || (state.activeWorkspace === null && (state.isLoadingWorkspaces || state.workspaces.length > 0))),
  )
  const myRole = useAppStore((state) => state.myRole)
  useWorkspacePresence(activeWorkspace?.id ?? null)

  const setActiveProject = useAppStore((state) => state.setActiveProject)
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)
  const setCommandPaletteOpen = useAppStore((state) => state.setCommandPaletteOpen)

  const [collapsedProject, setCollapsedProject] = useState<string | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  const expandFolder = useCallback((id: string) => {
    setExpandedFolders((current) => (current.has(id) ? current : new Set([...current, id])))
  }, [])

  const toggleFolder = useCallback((id: string) => {
    setExpandedFolders((current) => {
      const next = new Set(current)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const actions = useTreeActions(expandFolder)
  const index = useMemo(() => buildTreeIndex(folders, diagrams), [folders, diagrams])

  // Reveal the active diagram in the tree by expanding every folder above it.
  const [revealed, setRevealed] = useState<RevealedFor | null>(null)
  if (
    revealed === null ||
    revealed.activeDiagramId !== activeDiagramId ||
    revealed.activeFolderId !== activeFolderId ||
    revealed.folders !== folders
  ) {
    setRevealed({ activeDiagramId, activeFolderId, folders })
    const ancestors = folderAncestors(folders, activeFolderId)
    if (ancestors.length > 0 && !ancestors.every((id) => expandedFolders.has(id))) {
      setExpandedFolders(new Set([...expandedFolders, ...ancestors]))
    }
  }

  async function handleSelectProject(project: Project): Promise<void> {
    if (activeProject?.id === project.id) {
      setCollapsedProject((current) => (current === project.id ? null : project.id))
      return
    }
    setCollapsedProject(null)
    const hadDiagram = activeDiagramId !== null
    const loading = setActiveProject(project)
    if (hadDiagram) {
      navigate('/')
    }
    await loading
  }

  const view: TreeViewProps = { index, expandedFolders, toggleFolder, activeDiagramId, actions }

  return (
    // Viewers can browse but not change anything; the API enforces the same rule.
    <aside className="sidebar" data-readonly={myRole === 'viewer'}>
      <div className="sidebar-header">
        <WorkspaceSwitcher />
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
          data-active={activeDiagramId === null && activeProject !== null}
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
            data-edit-only
            data-tooltip="New project"
            disabled={activeWorkspace === null}
            onClick={() => void actions.createProject()}
          >
            <Plus size={14} />
          </button>
        </div>
        <LoadingGate loading={isLoadingProjectList} fallback={<ProjectListSkeleton />}>
          {projects.map((project) => {
            const isActive = activeProject?.id === project.id
            return (
              <ProjectNode
                key={project.id}
                project={project}
                isActive={isActive}
                isExpanded={isActive && collapsedProject !== project.id}
                isLoading={isLoadingProject}
                onSelect={(selected) => void handleSelectProject(selected)}
                view={view}
              />
            )
          })}
          {activeWorkspace !== null && projects.length === 0 ? (
            <div className="tree-empty">
              No projects ·{' '}
              <button type="button" onClick={() => void actions.createProject()}>
                Create one
              </button>
            </div>
          ) : null}
        </LoadingGate>
      </div>

      <SidebarFooter />
    </aside>
  )
}
