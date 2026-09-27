import MDEditor from '@uiw/react-md-editor'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'

export default function DocsPanel() {
  const documentation = useAppStore((state) => state.documentation)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const saveDocumentation = useAppStore((state) => state.saveDocumentation)
  const toggleDocsPanel = useAppStore((state) => state.toggleDocsPanel)

  const [content, setContent] = useState(documentation?.content ?? '')
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
    <aside
      data-color-mode="dark"
      style={{
        width: 320,
        flexShrink: 0,
        height: '100%',
        background: '#161b22',
        borderLeft: '1px solid #30363d',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 12px',
          borderBottom: '1px solid #30363d',
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        <span>📝 Documentation</span>
        <button
          type="button"
          onClick={toggleDocsPanel}
          style={{
            background: 'transparent',
            color: '#8b949e',
            border: 'none',
            cursor: 'pointer',
            fontSize: 14,
          }}
        >
          ✕
        </button>
      </header>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <MDEditor
          value={content}
          onChange={(value) => setContent(value ?? '')}
          height="100%"
          preview="edit"
          visibleDragbar={false}
        />
      </div>
    </aside>
  )
}
