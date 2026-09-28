import { Database, Globe, ListOrdered, Monitor, MousePointerClick, Router, Server, Shapes, Zap } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import type { SemanticType } from '../../api/types'
import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'
import EmptyState from '../ui/EmptyState'

const SEMANTIC_TYPES: { value: SemanticType; icon: typeof Server }[] = [
  { value: 'service', icon: Server },
  { value: 'database', icon: Database },
  { value: 'queue', icon: ListOrdered },
  { value: 'gateway', icon: Router },
  { value: 'client', icon: Monitor },
  { value: 'cache', icon: Zap },
  { value: 'external', icon: Globe },
  { value: 'custom', icon: Shapes },
]

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
      <EmptyState
        icon={<MousePointerClick size={20} />}
        title="Select a shape"
        description="Pick a single shape on the canvas to describe what it is. Types power the architecture validation."
      />
    )
  }

  const meta = semanticMetadata[selectedId] ?? {}

  return (
    <div className="panel-content scroll">
      <div className="field">
        <span className="field-label">Component type</span>
        <div className="type-grid">
          {SEMANTIC_TYPES.map(({ value, icon: Icon }) => (
            <button
              key={value}
              type="button"
              className="type-option"
              aria-pressed={meta.type === value}
              onClick={() => updateShapeMetadata(selectedId, { type: meta.type === value ? undefined : value })}
            >
              <Icon size={17} />
              {value}
            </button>
          ))}
        </div>
      </div>
      <div className="field">
        <label className="field-label" htmlFor="meta-label">
          Label
        </label>
        <input
          id="meta-label"
          className="input"
          placeholder="e.g. Orders API"
          value={meta.label ?? ''}
          onChange={(event) => updateShapeMetadata(selectedId, { label: event.target.value })}
        />
      </div>
      <div className="field">
        <label className="field-label" htmlFor="meta-technology">
          Technology
        </label>
        <input
          id="meta-technology"
          className="input"
          placeholder="e.g. Python, PostgreSQL, Kafka"
          value={meta.technology ?? ''}
          onChange={(event) => updateShapeMetadata(selectedId, { technology: event.target.value })}
        />
      </div>
      <div className="field">
        <label className="field-label" htmlFor="meta-notes">
          Notes
        </label>
        <textarea
          id="meta-notes"
          className="textarea"
          placeholder="Responsibilities, owners, SLAs…"
          value={meta.notes ?? ''}
          onChange={(event) => updateShapeMetadata(selectedId, { notes: event.target.value })}
        />
      </div>
    </div>
  )
}
