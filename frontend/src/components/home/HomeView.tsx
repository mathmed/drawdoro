import {
  BookOpenText,
  FilePlus2,
  Folder as FolderIcon,
  FolderPlus,
  Loader2,
  MoreHorizontal,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
  Users,
  Workflow,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import type { Diagram } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog, promptDialog } from '../../store/useDialogStore'
import { slugify, timeAgo } from '../../utils/format'
import EmptyState from '../ui/EmptyState'
import Logo from '../ui/Logo'
import Menu from '../ui/Menu'

const FEATURES = [
  { icon: Workflow, title: 'Draw', description: 'Sketch architecture on an infinite canvas.' },
  { icon: BookOpenText, title: 'Document', description: 'Docs live next to each diagram.' },
  { icon: Users, title: 'Collaborate', description: 'Edit together in real time and comment on shapes.' },
]

function WelcomeHero() {
  const createWorkspace = useAppStore((state) => state.createWorkspace)

  async function handleCreate(): Promise<void> {
    const name = await promptDialog({
      title: 'Create your workspace',
      description: 'A workspace groups your team’s projects. You can create more later.',
      label: 'Workspace name',
      placeholder: 'e.g. Platform Engineering',
    })
    if (name !== null) {
      await createWorkspace(name, slugify(name) || `workspace-${Date.now()}`)
    }
  }

  return (
    <div className="home scroll">
      <div className="hero">
        <Logo size={56} />
        <h1 className="hero-title">Welcome to Drawdoro</h1>
        <p className="hero-description">
          Architecture diagrams, documentation and decisions — together in one place.
        </p>
        <button type="button" className="btn btn-primary btn-lg" onClick={() => void handleCreate()}>
          <Plus size={16} /> Create a workspace
        </button>
      </div>
      <div className="feature-list" style={{ margin: '40px auto 0', padding: '0 24px' }}>
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <div key={title} className="feature">
            <Icon size={18} />
            <div className="feature-title">{title}</div>
            <div className="feature-description">{description}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function NoProjects() {
  const activeWorkspace = useAppStore((state) => state.activeWorkspace)
  const createProject = useAppStore((state) => state.createProject)

  async function handleCreate(): Promise<void> {
    const name = await promptDialog({
      title: 'New project',
      description: 'Projects hold the diagrams, docs and decisions for a system.',
      label: 'Name',
      placeholder: 'e.g. Payments platform',
    })
    if (name !== null) {
      await createProject(name)
    }
  }

  return (
    <div className="home scroll">
      <div className="hero">
        <Logo size={56} />
        <h1 className="hero-title">Start your first project</h1>
        <p className="hero-description">
          <strong>{activeWorkspace?.name}</strong> has no projects yet. Create one to start drawing
          diagrams.
        </p>
        <button type="button" className="btn btn-primary btn-lg" onClick={() => void handleCreate()}>
          <Plus size={16} /> New project
        </button>
      </div>
    </div>
  )
}

function DiagramCard({ diagram, folderName }: { diagram: Diagram; folderName: string | null }) {
  const navigate = useNavigate()
  const renameDiagram = useAppStore((state) => state.renameDiagram)
  const deleteDiagram = useAppStore((state) => state.deleteDiagram)

  async function handleRename(): Promise<void> {
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

  async function handleDelete(): Promise<void> {
    const confirmed = await confirmDialog({
      title: `Delete “${diagram.name}”?`,
      description: 'The diagram, its documentation and comments will be permanently deleted.',
      confirmLabel: 'Delete diagram',
      danger: true,
    })
    if (confirmed) {
      await deleteDiagram(diagram)
    }
  }

  return (
    <div
      className="diagram-card"
      role="link"
      tabIndex={0}
      onClick={() => navigate(`/diagrams/${diagram.id}`)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          navigate(`/diagrams/${diagram.id}`)
        }
      }}
    >
      <div className="diagram-card-preview">
        <Workflow size={30} strokeWidth={1.5} />
      </div>
      <div className="diagram-card-body">
        <span className="diagram-card-name">{diagram.name}</span>
        <span className="diagram-card-meta">
          {folderName !== null ? (
            <>
              <FolderIcon size={12} /> {folderName} ·
            </>
          ) : null}
          {diagram.updated_at !== undefined ? `Edited ${timeAgo(diagram.updated_at)}` : 'New'}
        </span>
      </div>
      <div className="diagram-card-menu">
        <Menu
          align="end"
          items={[
            { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void handleRename() },
            { kind: 'separator' },
            { label: 'Delete', icon: <Trash2 size={15} />, danger: true, onSelect: () => void handleDelete() },
          ]}
          trigger={({ toggle }) => (
            <button
              type="button"
              className="btn btn-ghost btn-icon btn-sm"
              aria-label="Diagram actions"
              onClick={(event) => {
                event.stopPropagation()
                toggle()
              }}
            >
              <MoreHorizontal size={15} />
            </button>
          )}
        />
      </div>
    </div>
  )
}

export default function HomeView() {
  const isLoadingWorkspaces = useAppStore((state) => state.isLoadingWorkspaces)
  const workspaces = useAppStore((state) => state.workspaces)
  const activeWorkspace = useAppStore((state) => state.activeWorkspace)
  const projects = useAppStore((state) => state.projects)
  const activeProject = useAppStore((state) => state.activeProject)
  const folders = useAppStore((state) => state.folders)
  const diagrams = useAppStore((state) => state.diagrams)
  const isLoadingProject = useAppStore((state) => state.isLoadingProject)
  const openNewDiagram = useAppStore((state) => state.openNewDiagram)
  const createFolder = useAppStore((state) => state.createFolder)

  if (isLoadingWorkspaces && workspaces.length === 0) {
    return (
      <div className="full-center">
        <Loader2 size={16} className="spinner" /> Loading…
      </div>
    )
  }
  if (workspaces.length === 0) {
    return <WelcomeHero />
  }
  if (activeWorkspace !== null && projects.length === 0) {
    return <NoProjects />
  }
  if (activeProject === null) {
    return (
      <div className="full-center">
        <Loader2 size={16} className="spinner" />
      </div>
    )
  }

  async function handleNewFolder(): Promise<void> {
    const name = await promptDialog({ title: 'New folder', label: 'Name', placeholder: 'e.g. Services' })
    if (name !== null) {
      await createFolder(name)
    }
  }

  const sorted = [...diagrams].sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? ''))
  const folderName = (id: string | null): string | null =>
    folders.find((folder) => folder.id === id)?.name ?? null

  return (
    <div className="home scroll">
      <div className="home-inner">
        <div className="home-header">
          <div>
            <div className="home-eyebrow">{activeWorkspace?.name}</div>
            <h1 className="home-title">{activeProject.name}</h1>
            <p className="home-description">
              {activeProject.description !== null && activeProject.description !== ''
                ? activeProject.description
                : `${diagrams.length} diagram${diagrams.length === 1 ? '' : 's'} · ${folders.length} folder${folders.length === 1 ? '' : 's'}`}
            </p>
          </div>
          <div className="home-actions">
            <button type="button" className="btn btn-secondary" onClick={() => void handleNewFolder()}>
              <FolderPlus size={15} /> New folder
            </button>
            <button type="button" className="btn btn-primary" onClick={() => openNewDiagram()}>
              <FilePlus2 size={15} /> New diagram
            </button>
          </div>
        </div>

        {isLoadingProject && diagrams.length === 0 ? (
          <div className="full-center" style={{ height: 200 }}>
            <Loader2 size={16} className="spinner" />
          </div>
        ) : sorted.length === 0 ? (
          <div style={{ border: '1px dashed var(--border-strong)', borderRadius: 'var(--radius-xl)', padding: 24 }}>
            <EmptyState
              icon={<Sparkles size={20} />}
              title="No diagrams yet"
              description="Create your first diagram to start drawing the architecture of this project."
              action={
                <button type="button" className="btn btn-primary" onClick={() => openNewDiagram()}>
                  <Plus size={15} /> Create diagram
                </button>
              }
            />
          </div>
        ) : (
          <>
            <div className="home-section-title">Recent diagrams</div>
            <div className="card-grid">
              <button type="button" className="new-card" onClick={() => openNewDiagram()}>
                <Plus size={20} /> New diagram
              </button>
              {sorted.map((diagram) => (
                <DiagramCard key={diagram.id} diagram={diagram} folderName={folderName(diagram.folder_id)} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
