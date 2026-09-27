import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { Diagram, Folder, Project } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

const rowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  fontSize: 13,
  padding: '3px 4px',
  borderRadius: 4,
  cursor: 'pointer',
  userSelect: 'none',
}

const addButtonStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: '#8b949e',
  cursor: 'pointer',
  fontSize: 12,
  padding: '0 2px',
}

export default function Sidebar() {
  const navigate = useNavigate()

  const workspaces = useAppStore((state) => state.workspaces)
  const activeWorkspace = useAppStore((state) => state.activeWorkspace)
  const projects = useAppStore((state) => state.projects)
  const activeProject = useAppStore((state) => state.activeProject)
  const folders = useAppStore((state) => state.folders)
  const diagrams = useAppStore((state) => state.diagrams)
  const activeDiagram = useAppStore((state) => state.activeDiagram)

  const setActiveWorkspace = useAppStore((state) => state.setActiveWorkspace)
  const setActiveProject = useAppStore((state) => state.setActiveProject)
  const setActiveDiagram = useAppStore((state) => state.setActiveDiagram)
  const createWorkspace = useAppStore((state) => state.createWorkspace)
  const createProject = useAppStore((state) => state.createProject)
  const createFolder = useAppStore((state) => state.createFolder)
  const createDiagram = useAppStore((state) => state.createDiagram)

  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  function toggle(set: Set<string>, id: string): Set<string> {
    const next = new Set(set)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    return next
  }

  async function handleSelectWorkspace(id: string): Promise<void> {
    const workspace = workspaces.find((item) => item.id === id)
    if (workspace !== undefined) {
      await setActiveWorkspace(workspace)
    }
  }

  async function handleCreateWorkspace(): Promise<void> {
    const name = window.prompt('Workspace name')?.trim()
    if (name === undefined || name === '') {
      return
    }
    const slug = window.prompt('Workspace slug', slugify(name))?.trim()
    if (slug === undefined || slug === '') {
      return
    }
    await createWorkspace(name, slug)
  }

  async function handleCreateProject(): Promise<void> {
    const name = window.prompt('Project name')?.trim()
    if (name === undefined || name === '') {
      return
    }
    await createProject(name)
  }

  async function handleExpandProject(project: Project): Promise<void> {
    if (activeProject?.id !== project.id) {
      await setActiveProject(project)
    }
    setExpandedProjects((current) => toggle(current, project.id))
  }

  async function handleCreateFolder(parentId?: string): Promise<void> {
    const name = window.prompt('Folder name')?.trim()
    if (name === undefined || name === '') {
      return
    }
    await createFolder(name, parentId)
  }

  async function handleCreateDiagram(folderId?: string): Promise<void> {
    const name = window.prompt('Diagram name')?.trim()
    if (name === undefined || name === '') {
      return
    }
    const diagram = await createDiagram(name, folderId)
    if (diagram !== null) {
      await setActiveDiagram(diagram)
      navigate(`/diagrams/${diagram.id}`)
    }
  }

  async function handleOpenDiagram(diagram: Diagram): Promise<void> {
    await setActiveDiagram(diagram)
    navigate(`/diagrams/${diagram.id}`)
  }

  function childFolders(parentId: string | null): Folder[] {
    return folders.filter((folder) => folder.parent_folder_id === parentId)
  }

  function folderDiagrams(folderId: string | null): Diagram[] {
    return diagrams.filter((diagram) => diagram.folder_id === folderId)
  }

  function renderFolder(folder: Folder, depth: number): React.ReactNode {
    const isExpanded = expandedFolders.has(folder.id)
    return (
      <div key={folder.id}>
        <div style={{ ...rowStyle, paddingLeft: 8 + depth * 12 }}>
          <span
            style={{ flex: 1 }}
            onClick={() => setExpandedFolders((current) => toggle(current, folder.id))}
          >
            {isExpanded ? '📂' : '📁'} {folder.name}
          </span>
          <button
            type="button"
            title="New subfolder"
            style={addButtonStyle}
            onClick={() => void handleCreateFolder(folder.id)}
          >
            📁+
          </button>
          <button
            type="button"
            title="New diagram"
            style={addButtonStyle}
            onClick={() => void handleCreateDiagram(folder.id)}
          >
            📄+
          </button>
        </div>
        {isExpanded ? (
          <div>
            {childFolders(folder.id).map((child) => renderFolder(child, depth + 1))}
            {folderDiagrams(folder.id).map((diagram) => renderDiagram(diagram, depth + 1))}
          </div>
        ) : null}
      </div>
    )
  }

  function renderDiagram(diagram: Diagram, depth: number): React.ReactNode {
    const isActive = activeDiagram?.id === diagram.id
    return (
      <div
        key={diagram.id}
        style={{
          ...rowStyle,
          paddingLeft: 8 + depth * 12,
          background: isActive ? '#1f6feb33' : 'transparent',
          color: isActive ? '#e6edf3' : '#c9d1d9',
        }}
        onClick={() => void handleOpenDiagram(diagram)}
      >
        📄 {diagram.name}
      </div>
    )
  }

  function renderProject(project: Project): React.ReactNode {
    const isExpanded = expandedProjects.has(project.id) && activeProject?.id === project.id
    return (
      <div key={project.id}>
        <div style={{ ...rowStyle, fontWeight: 600 }}>
          <span style={{ flex: 1 }} onClick={() => void handleExpandProject(project)}>
            {isExpanded ? '▾' : '▸'} {project.name}
          </span>
          <button
            type="button"
            title="New folder"
            style={addButtonStyle}
            onClick={() => void handleCreateFolder()}
          >
            📁+
          </button>
          <button
            type="button"
            title="New diagram"
            style={addButtonStyle}
            onClick={() => void handleCreateDiagram()}
          >
            📄+
          </button>
        </div>
        {isExpanded ? (
          <div>
            {childFolders(null).map((folder) => renderFolder(folder, 1))}
            {folderDiagrams(null).map((diagram) => renderDiagram(diagram, 1))}
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <aside
      style={{
        width: 250,
        flexShrink: 0,
        height: '100%',
        background: '#161b22',
        borderRight: '1px solid #30363d',
        display: 'flex',
        flexDirection: 'column',
        color: '#e6edf3',
      }}
    >
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #30363d' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <select
            value={activeWorkspace?.id ?? ''}
            onChange={(event) => void handleSelectWorkspace(event.target.value)}
            style={{
              flex: 1,
              background: '#0f1117',
              color: '#e6edf3',
              border: '1px solid #30363d',
              borderRadius: 6,
              padding: '5px 6px',
              fontSize: 13,
            }}
          >
            {workspaces.length === 0 ? <option value="">No workspaces</option> : null}
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            title="New workspace"
            onClick={() => void handleCreateWorkspace()}
            style={{
              background: '#21262d',
              color: '#e6edf3',
              border: '1px solid #30363d',
              borderRadius: 6,
              padding: '5px 8px',
              cursor: 'pointer',
            }}
          >
            +
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '8px 6px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 4px 4px',
            fontSize: 11,
            textTransform: 'uppercase',
            letterSpacing: 0.5,
            color: '#8b949e',
          }}
        >
          <span>Projects</span>
          <button
            type="button"
            title="New project"
            style={addButtonStyle}
            disabled={activeWorkspace === null}
            onClick={() => void handleCreateProject()}
          >
            +
          </button>
        </div>
        {projects.map((project) => renderProject(project))}
      </div>
    </aside>
  )
}
