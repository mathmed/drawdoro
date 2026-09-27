import { useEffect, useRef, useState } from 'react'

import type { SemanticType } from '../../api/types'
import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'

const SEMANTIC_TYPES: SemanticType[] = [
  'service',
  'database',
  'queue',
  'gateway',
  'client',
  'cache',
  'external',
  'custom',
]

const inputStyle: React.CSSProperties = {
  background: '#0f1117',
  color: '#e6edf3',
  border: '1px solid #30363d',
  borderRadius: 6,
  padding: '6px 8px',
  fontSize: 13,
  width: '100%',
  boxSizing: 'border-box',
}

const labelStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#8b949e',
  marginBottom: 4,
  display: 'block',
}

export default function SemanticPanel() {
  const editor = useAppStore((state) => state.editor)
  const semanticMetadata = useAppStore((state) => state.semanticMetadata)
  const updateShapeMetadata = useAppStore((state) => state.updateShapeMetadata)
  const saveSemanticMetadata = useAppStore((state) => state.saveSemanticMetadata)

  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    if (editor === null) {
      return
    }
    function update(): void {
      if (editor === null) {
        return
      }
      setSelectedId(editor.getOnlySelectedShapeId())
    }
    update()
    const unlisten = editor.store.listen(update, { scope: 'session' })
    return unlisten
  }, [editor])

  const debounced = useDebounce(semanticMetadata, 1000)
  const skipFirst = useRef(true)
  useEffect(() => {
    if (skipFirst.current) {
      skipFirst.current = false
      return
    }
    void saveSemanticMetadata()
  }, [debounced, saveSemanticMetadata])

  if (selectedId === null) {
    return (
      <div style={{ padding: 16, color: '#8b949e', fontSize: 13 }}>
        Select a shape on the canvas to edit its metadata.
      </div>
    )
  }

  const meta = semanticMetadata[selectedId] ?? {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 12 }}>
      <div>
        <label style={labelStyle}>Type</label>
        <select
          style={inputStyle}
          value={meta.type ?? ''}
          onChange={(e) =>
            updateShapeMetadata(selectedId, {
              type: e.target.value === '' ? undefined : (e.target.value as SemanticType),
            })
          }
        >
          <option value="">— none —</option>
          {SEMANTIC_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label style={labelStyle}>Label</label>
        <input
          style={inputStyle}
          value={meta.label ?? ''}
          onChange={(e) => updateShapeMetadata(selectedId, { label: e.target.value })}
        />
      </div>
      <div>
        <label style={labelStyle}>Technology</label>
        <input
          style={inputStyle}
          value={meta.technology ?? ''}
          placeholder="Python, PostgreSQL, ..."
          onChange={(e) => updateShapeMetadata(selectedId, { technology: e.target.value })}
        />
      </div>
      <div>
        <label style={labelStyle}>Notes</label>
        <textarea
          style={{ ...inputStyle, resize: 'vertical', minHeight: 60 }}
          value={meta.notes ?? ''}
          onChange={(e) => updateShapeMetadata(selectedId, { notes: e.target.value })}
        />
      </div>
    </div>
  )
}
