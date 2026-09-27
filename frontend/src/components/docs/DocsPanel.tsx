import MDEditor from '@uiw/react-md-editor'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'

export default function DocsPanel() {
  const documentation = useAppStore((state) => state.documentation)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const saveDocumentation = useAppStore((state) => state.saveDocumentation)

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
    <div data-color-mode="dark" style={{ flex: 1, overflow: 'auto' }}>
      <MDEditor
        value={content}
        onChange={(value) => setContent(value ?? '')}
        height="100%"
        preview="edit"
        visibleDragbar={false}
      />
    </div>
  )
}
