import MDEditor, { commands } from '@uiw/react-md-editor'
import { Eye, PencilLine } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'
import { useThemeStore } from '../../store/useThemeStore'
import LoadingGate from '../ui/loading/LoadingGate'
import { Skeleton, SkeletonGroup } from '../ui/loading/Skeleton'

const PLACEHOLDER = `# Overview

Describe what this diagram shows, its main components and how they interact.

## Components

## Data flow
`

const TOOLBAR = [
  commands.title2,
  commands.bold,
  commands.italic,
  commands.strikethrough,
  commands.divider,
  commands.link,
  commands.quote,
  commands.code,
  commands.codeBlock,
  commands.divider,
  commands.unorderedListCommand,
  commands.orderedListCommand,
  commands.checkedListCommand,
  commands.table,
]

const SKELETON_LINES = ['42%', '92%', '86%', '64%', '0', '36%', '88%', '72%']

// Mirrors the editor (toolbar and text) so nothing moves when the page arrives.
function DocsSkeleton() {
  return (
    <SkeletonGroup label="Loading documentation" className="docs-skeleton">
      <div className="docs-skeleton-toolbar">
        {Array.from({ length: 7 }, (_, index) => (
          <Skeleton key={index} width={18} height={18} radius={4} />
        ))}
      </div>
      <div className="docs-skeleton-text">
        {SKELETON_LINES.map((width, index) =>
          width === '0' ? (
            <span key={index} className="docs-skeleton-gap" />
          ) : (
            <Skeleton key={index} className="skeleton-line" width={width} height={index === 0 || index === 5 ? 14 : 10} />
          ),
        )}
      </div>
    </SkeletonGroup>
  )
}

export default function DocsPanel() {
  const documentation = useAppStore((state) => state.documentation)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const saveDocumentation = useAppStore((state) => state.saveDocumentation)
  const theme = useThemeStore((state) => state.resolved)
  // Until the page arrives the editor is not shown, so nothing typed can be overwritten by it.
  const isLoading = useAppStore((state) => state.isLoadingDiagramDetails && state.documentation === null)

  const [content, setContent] = useState(documentation?.content ?? '')
  const [mode, setMode] = useState<'write' | 'preview'>('write')
  const debounced = useDebounce(content, 1000)
  const lastSaved = useRef(documentation?.content ?? '')
  const [shownPage, setShownPage] = useState({ documentation, diagramId: activeDiagram?.id })

  // Reset the editor when switching diagrams or when the stored page changes.
  if (shownPage.documentation !== documentation || shownPage.diagramId !== activeDiagram?.id) {
    setShownPage({ documentation, diagramId: activeDiagram?.id })
    setContent(documentation?.content ?? '')
  }

  useEffect(() => {
    lastSaved.current = documentation?.content ?? ''
  }, [documentation, activeDiagram?.id])

  useEffect(() => {
    if (debounced !== lastSaved.current) {
      lastSaved.current = debounced
      void saveDocumentation(debounced)
    }
  }, [debounced, saveDocumentation])

  return (
    <>
      <div className="panel-toolbar">
        <span className="panel-toolbar-title">Markdown</span>
        <div className="segmented">
          <button type="button" aria-pressed={mode === 'write'} onClick={() => setMode('write')}>
            <PencilLine size={13} /> Write
          </button>
          <button type="button" aria-pressed={mode === 'preview'} onClick={() => setMode('preview')}>
            <Eye size={13} /> Preview
          </button>
        </div>
      </div>
      <LoadingGate loading={isLoading} fallback={<DocsSkeleton />}>
        {mode === 'write' ? (
          <div className="docs-editor" data-color-mode={theme}>
            <MDEditor
              value={content}
              onChange={(value) => setContent(value ?? '')}
              height="100%"
              preview="edit"
              visibleDragbar={false}
              commands={TOOLBAR}
              extraCommands={[]}
              textareaProps={{ placeholder: PLACEHOLDER }}
            />
          </div>
        ) : (
          <div className="docs-preview scroll" data-color-mode={theme}>
            {content.trim() === '' ? (
              <p style={{ color: 'var(--text-subtle)', fontSize: 13 }}>Nothing written yet.</p>
            ) : (
              <MDEditor.Markdown source={content} />
            )}
          </div>
        )}
      </LoadingGate>
    </>
  )
}
