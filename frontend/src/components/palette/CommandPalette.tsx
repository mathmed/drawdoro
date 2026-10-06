import {
  BookmarkPlus,
  BookOpenText,
  FilePlus2,
  FolderPlus,
  House,
  Image,
  Images,
  Layers,
  MessageSquare,
  Moon,
  MousePointer2,
  PanelLeft,
  Play,
  Search,
  ShieldCheck,
  Sun,
  Tags,
  Workflow,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'

import { useAppStore } from '../../store/useAppStore'
import { promptDialog } from '../../store/useDialogStore'
import { useThemeStore } from '../../store/useThemeStore'
import { exportDiagram } from '../../utils/exportDiagram'
import { modKey } from '../../utils/format'
import { canSaveSelection, saveSelectionToGallery } from '../../utils/gallery'
import { canRunSelection, runSelection, SELECTION_COMMANDS } from '../../utils/shapeSelection'

interface Command {
  id: string
  group: 'Diagrams' | 'Projects' | 'Actions' | 'Selection'
  label: string
  icon: ReactNode
  hint?: string
  run: () => void
}

function matches(query: string, label: string): boolean {
  const normalizedQuery = query.toLowerCase().trim()
  if (normalizedQuery === '') {
    return true
  }
  return label.toLowerCase().includes(normalizedQuery)
}

export default function CommandPalette() {
  const navigate = useNavigate()
  const setOpen = useAppStore((state) => state.setCommandPaletteOpen)
  const diagrams = useAppStore((state) => state.diagrams)
  const projects = useAppStore((state) => state.projects)
  const activeProject = useAppStore((state) => state.activeProject)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const editor = useAppStore((state) => state.editor)
  const resolvedTheme = useThemeStore((state) => state.resolved)

  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(0)
  const listRef = useRef<HTMLDivElement>(null)

  const commands = useMemo<Command[]>(() => {
    const store = useAppStore.getState()
    const list: Command[] = diagrams.map((diagram) => ({
      id: `diagram-${diagram.id}`,
      group: 'Diagrams',
      label: diagram.name,
      icon: <Workflow size={16} />,
      hint: diagram.id === activeDiagram?.id ? 'Open' : undefined,
      run: () => navigate(`/diagrams/${diagram.id}`),
    }))

    for (const project of projects) {
      if (project.id === activeProject?.id) {
        continue
      }
      list.push({
        id: `project-${project.id}`,
        group: 'Projects',
        label: `Switch to ${project.name}`,
        icon: <Layers size={16} />,
        run: () => {
          void store.setActiveProject(project)
          navigate('/')
        },
      })
    }

    const actions: Command[] = [
      {
        id: 'new-diagram',
        group: 'Actions',
        label: 'New diagram',
        icon: <FilePlus2 size={16} />,
        run: () => store.openNewDiagram(),
      },
      {
        id: 'new-folder',
        group: 'Actions',
        label: 'New folder',
        icon: <FolderPlus size={16} />,
        run: () => {
          void promptDialog({ title: 'New folder', label: 'Name', placeholder: 'e.g. Services' }).then((name) => {
            if (name !== null) {
              void store.createFolder(name)
            }
          })
        },
      },
      {
        id: 'overview',
        group: 'Actions',
        label: 'Go to project overview',
        icon: <House size={16} />,
        run: () => navigate('/'),
      },
      {
        id: 'toggle-sidebar',
        group: 'Actions',
        label: 'Toggle sidebar',
        icon: <PanelLeft size={16} />,
        hint: `${modKey} \\`,
        run: store.toggleSidebar,
      },
      {
        id: 'toggle-theme',
        group: 'Actions',
        label: resolvedTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme',
        icon: resolvedTheme === 'dark' ? <Sun size={16} /> : <Moon size={16} />,
        run: () => useThemeStore.getState().setPreference(resolvedTheme === 'dark' ? 'light' : 'dark'),
      },
    ]

    if (activeDiagram !== null) {
      actions.push(
        {
          id: 'toggle-inspector',
          group: 'Actions',
          label: 'Toggle details panel',
          icon: <PanelLeft size={16} style={{ transform: 'scaleX(-1)' }} />,
          hint: `${modKey} ⇧ .`,
          run: store.toggleInspector,
        },
        { id: 'properties', group: 'Actions', label: 'Open shape properties', icon: <Tags size={16} />, run: () => store.openInspector('properties') },
        { id: 'docs', group: 'Actions', label: 'Open documentation', icon: <BookOpenText size={16} />, run: () => store.openInspector('docs') },
        { id: 'comments', group: 'Actions', label: 'Open comments', icon: <MessageSquare size={16} />, run: () => store.openInspector('comments') },
        { id: 'gallery', group: 'Actions', label: 'Open gallery', icon: <Images size={16} />, run: () => store.openInspector('gallery') },
        { id: 'validate', group: 'Actions', label: 'Validate architecture', icon: <ShieldCheck size={16} />, run: store.runValidation },
        { id: 'present', group: 'Actions', label: 'Start presentation', icon: <Play size={16} />, run: store.enterPresentation },
        {
          id: 'export-png',
          group: 'Actions',
          label: 'Export as PNG',
          icon: <Image size={16} />,
          run: () => void exportDiagram('png', activeDiagram, editor),
        },
        {
          id: 'export-svg',
          group: 'Actions',
          label: 'Export as SVG',
          icon: <Image size={16} />,
          run: () => void exportDiagram('svg', activeDiagram, editor),
        },
      )
    }

    const selection: Command[] =
      editor === null
        ? []
        : SELECTION_COMMANDS.filter(({ command }) => canRunSelection(command, editor)).map((entry) => ({
            id: `select-${entry.command}`,
            group: 'Selection',
            label: entry.label,
            icon: <MousePointer2 size={16} />,
            hint: entry.hint,
            run: () => runSelection(entry.command, editor, useAppStore.getState().semanticMetadata),
          }))

    if (editor !== null && canSaveSelection(editor)) {
      selection.push({
        id: 'save-to-gallery',
        group: 'Selection',
        label: 'Save selection to gallery',
        icon: <BookmarkPlus size={16} />,
        run: () => void saveSelectionToGallery(editor),
      })
    }

    return [...list, ...actions, ...selection]
  }, [diagrams, projects, activeProject, activeDiagram, editor, resolvedTheme, navigate])

  const filtered = commands.filter((command) => matches(query, command.label))

  useEffect(() => {
    listRef.current?.querySelector('[data-selected="true"]')?.scrollIntoView({ block: 'nearest' })
  }, [selected])

  function run(command: Command): void {
    setOpen(false)
    command.run()
  }

  function handleKeyDown(event: React.KeyboardEvent): void {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setSelected((index) => Math.min(index + 1, filtered.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setSelected((index) => Math.max(index - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      const command = filtered[selected]
      if (command !== undefined) {
        run(command)
      }
    } else if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
    }
  }

  let previousGroup: string | null = null

  return createPortal(
    <div className="modal-overlay" onMouseDown={() => setOpen(false)}>
      <div className="palette" role="dialog" aria-label="Command palette" onMouseDown={(event) => event.stopPropagation()}>
        <div className="palette-input-row">
          <Search size={17} />
          <input
            className="palette-input"
            autoFocus
            placeholder="Search diagrams and actions…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setSelected(0)
            }}
            onKeyDown={handleKeyDown}
          />
        </div>
        <div className="palette-list scroll" ref={listRef}>
          {filtered.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-description">No results for “{query}”</div>
            </div>
          ) : null}
          {filtered.map((command, index) => {
            const header = command.group !== previousGroup ? command.group : null
            previousGroup = command.group
            return (
              <div key={command.id}>
                {header !== null ? <div className="palette-group">{header}</div> : null}
                <button
                  type="button"
                  className="palette-item"
                  data-selected={index === selected}
                  onMouseMove={() => setSelected(index)}
                  onClick={() => run(command)}
                >
                  {command.icon}
                  <span>{command.label}</span>
                  {command.hint !== undefined ? <span className="palette-item-hint">{command.hint}</span> : null}
                </button>
              </div>
            )
          })}
        </div>
        <div className="palette-footer">
          <span>
            <kbd className="kbd">↑</kbd>
            <kbd className="kbd">↓</kbd> navigate
          </span>
          <span>
            <kbd className="kbd">↵</kbd> select
          </span>
          <span>
            <kbd className="kbd">esc</kbd> close
          </span>
        </div>
      </div>
    </div>,
    document.body,
  )
}
