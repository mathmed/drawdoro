import MDEditor, { commands } from '@uiw/react-md-editor'
import { Eye, PencilLine } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'
import { useThemeStore } from '../../store/useThemeStore'

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

export default function DocsPanel() {
  const documentation = useAppStore((state) => state.documentation)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const saveDocumentation = useAppStore((state) => state.saveDocumentation)
  const theme = useThemeStore((state) => state.resolved)

  const [content, setContent] = useState(documentation?.content ?? '')
  const [mode, setMode] = useState<'write' | 'preview'>('write')
  const debounced = useDebounce(content, 1000)
  const lastSaved = useRef(documentation?.content ?? '')

  // Reset the editor when switching diagrams or when the stored page changes.
  useEffect(() => {
    const stored = documentation?.content ?? ''
    setContent(stored)
    lastSaved.current = stored
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
    </>
  )
}
