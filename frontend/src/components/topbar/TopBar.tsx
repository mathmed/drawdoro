import {
  AlertCircle,
  Check,
  ChevronRight,
  Download,
  FileImage,
  FileJson,
  Image,
  Loader2,
  PanelLeftOpen,
  PanelRight,
  Play,
  ShieldCheck,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { Folder } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { exportDiagram, type ExportFormat } from '../../utils/exportDiagram'
import { modKey } from '../../utils/format'
import Menu from '../ui/Menu'

function folderPath(folders: Folder[], folderId: string | null): Folder[] {
  const path: Folder[] = []
  let current = folders.find((folder) => folder.id === folderId)
  while (current !== undefined) {
    path.unshift(current)
    const parentId = current.parent_folder_id
    current = folders.find((folder) => folder.id === parentId)
  }
  return path
}

function SaveIndicator() {
  const saveStatus = useAppStore((state) => state.saveStatus)

  if (saveStatus === 'idle') {
    return null
  }
  if (saveStatus === 'saving') {
    return (
      <span className="save-status" data-status="saving">
        <Loader2 size={13} className="spinner" /> Saving…
      </span>
    )
  }
  if (saveStatus === 'error') {
    return (
      <span className="save-status" data-status="error">
        <AlertCircle size={13} /> Not saved
      </span>
    )
  }
  return (
    <span className="save-status" data-status="saved">
      <Check size={13} /> Saved
    </span>
  )
}

function DiagramTitle() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const renameDiagram = useAppStore((state) => state.renameDiagram)
  const [name, setName] = useState(activeDiagram?.name ?? '')

  useEffect(() => {
    setName(activeDiagram?.name ?? '')
  }, [activeDiagram?.id, activeDiagram?.name])

  function commit(): void {
    const trimmed = name.trim()
    if (activeDiagram === null || trimmed === '' || trimmed === activeDiagram.name) {
      setName(activeDiagram?.name ?? '')
      return
    }
    void renameDiagram(trimmed)
  }

  return (
    <input
      className="title-input"
      aria-label="Diagram name"
      value={name}
      onChange={(event) => setName(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.currentTarget.blur()
        }
        if (event.key === 'Escape') {
          setName(activeDiagram?.name ?? '')
          event.currentTarget.blur()
        }
      }}
    />
  )
}

export default function TopBar() {
  const navigate = useNavigate()
  const activeProject = useAppStore((state) => state.activeProject)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const folders = useAppStore((state) => state.folders)
  const editor = useAppStore((state) => state.editor)
  const peers = useAppStore((state) => state.peers)
  const isSidebarOpen = useAppStore((state) => state.isSidebarOpen)
  const isInspectorOpen = useAppStore((state) => state.isInspectorOpen)
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)
  const toggleInspector = useAppStore((state) => state.toggleInspector)
  const runValidation = useAppStore((state) => state.runValidation)
  const enterPresentation = useAppStore((state) => state.enterPresentation)

  function handleExport(format: ExportFormat): void {
    if (activeDiagram !== null) {
      void exportDiagram(format, activeDiagram, editor)
    }
  }

  return (
    <header className="topbar">
      {!isSidebarOpen ? (
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          aria-label="Open sidebar"
          data-tooltip={`Open sidebar  ${modKey} \\`}
          onClick={toggleSidebar}
        >
          <PanelLeftOpen size={16} />
        </button>
      ) : null}

      <nav className="breadcrumbs" aria-label="Breadcrumb">
        {activeDiagram === null ? (
          <span className="page-title">{activeProject?.name ?? 'Drawdoro'}</span>
        ) : (
          <>
            {activeProject !== null ? (
              <button type="button" className="breadcrumb" onClick={() => navigate('/')}>
                {activeProject.name}
              </button>
            ) : null}
            {folderPath(folders, activeDiagram.folder_id).map((folder) => (
              <span key={folder.id} style={{ display: 'contents' }}>
                <ChevronRight size={14} className="breadcrumb-separator" />
                <span className="breadcrumb">{folder.name}</span>
              </span>
            ))}
            <ChevronRight size={14} className="breadcrumb-separator" />
            <DiagramTitle />
            <SaveIndicator />
          </>
        )}
      </nav>

      {activeDiagram !== null ? (
        <div className="topbar-actions">
          {peers > 1 ? (
            <span className="presence" title="People editing this diagram right now">
              <span className="presence-dot" />
              {peers} online
            </span>
          ) : null}
          {peers > 1 ? <span className="topbar-divider" /> : null}
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            data-tooltip="Check the architecture for issues"
            onClick={runValidation}
          >
            <ShieldCheck size={15} /> Validate
          </button>
          <Menu
            align="end"
            items={[
              { kind: 'label', label: 'Image' },
              { label: 'PNG', icon: <Image size={15} />, hint: '2x', onSelect: () => handleExport('png') },
              { label: 'SVG', icon: <FileImage size={15} />, hint: 'vector', onSelect: () => handleExport('svg') },
              { kind: 'label', label: 'Source' },
              { label: 'Canvas JSON', icon: <FileJson size={15} />, hint: '.json', onSelect: () => handleExport('json') },
            ]}
            trigger={({ open, toggle }) => (
              <button type="button" className="btn btn-ghost btn-sm" aria-pressed={open} onClick={toggle}>
                <Download size={15} /> Export
              </button>
            )}
          />
          <span className="topbar-divider" />
          <button type="button" className="btn btn-primary btn-sm" onClick={enterPresentation}>
            <Play size={14} /> Present
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-sm"
            aria-label="Toggle details panel"
            aria-pressed={isInspectorOpen}
            data-tooltip={`Properties, docs & comments  ${modKey} ⇧ .`}
            onClick={toggleInspector}
            style={{ marginLeft: 4 }}
          >
            <PanelRight size={16} />
          </button>
        </div>
      ) : null}
    </header>
  )
}
