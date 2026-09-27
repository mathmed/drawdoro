import { useEffect, useState } from 'react'

import { useAppStore } from '../../store/useAppStore'
import ExportMenu from './ExportMenu'

export default function Toolbar() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isDocsPanelOpen = useAppStore((state) => state.isDocsPanelOpen)
  const toggleDocsPanel = useAppStore((state) => state.toggleDocsPanel)
  const isCodePanelOpen = useAppStore((state) => state.isCodePanelOpen)
  const toggleCodePanel = useAppStore((state) => state.toggleCodePanel)
  const toggleTemplateModal = useAppStore((state) => state.toggleTemplateModal)
  const renameDiagram = useAppStore((state) => state.renameDiagram)

  const [name, setName] = useState(activeDiagram?.name ?? '')

  useEffect(() => {
    setName(activeDiagram?.name ?? '')
  }, [activeDiagram?.id, activeDiagram?.name])

  function commitName(): void {
    const trimmed = name.trim()
    if (activeDiagram === null || trimmed === '' || trimmed === activeDiagram.name) {
      setName(activeDiagram?.name ?? '')
      return
    }
    void renameDiagram(trimmed)
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: 8,
        right: 8,
        zIndex: 300,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: 8,
        padding: '6px 8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
      }}
    >
      <input
        value={name}
        onChange={(event) => setName(event.target.value)}
        onBlur={commitName}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.currentTarget.blur()
          }
        }}
        style={{
          background: '#0f1117',
          color: '#e6edf3',
          border: '1px solid #30363d',
          borderRadius: 6,
          padding: '4px 8px',
          fontSize: 13,
          width: 180,
        }}
      />
      <button
        type="button"
        onClick={toggleDocsPanel}
        style={{
          background: isDocsPanelOpen ? '#2f81f7' : '#21262d',
          color: '#e6edf3',
          border: '1px solid #30363d',
          borderRadius: 6,
          padding: '5px 10px',
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        📝 Docs
      </button>
      <button
        type="button"
        onClick={toggleCodePanel}
        style={{
          background: isCodePanelOpen ? '#2f81f7' : '#21262d',
          color: '#e6edf3',
          border: '1px solid #30363d',
          borderRadius: 6,
          padding: '5px 10px',
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        💻 Code
      </button>
      <button
        type="button"
        onClick={toggleTemplateModal}
        style={{
          background: '#21262d',
          color: '#e6edf3',
          border: '1px solid #30363d',
          borderRadius: 6,
          padding: '5px 10px',
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        📋 Templates
      </button>
      <ExportMenu />
    </div>
  )
}
