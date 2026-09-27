import { useEffect, useState } from 'react'

import { useAppStore } from '../../store/useAppStore'
import ValidationModal from '../semantic/ValidationModal'
import ExportMenu from './ExportMenu'

const buttonBase: React.CSSProperties = {
  color: '#e6edf3',
  border: '1px solid #30363d',
  borderRadius: 6,
  padding: '5px 10px',
  fontSize: 13,
  cursor: 'pointer',
}

export default function Toolbar() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isDocsPanelOpen = useAppStore((state) => state.isDocsPanelOpen)
  const toggleDocsPanel = useAppStore((state) => state.toggleDocsPanel)
  const isCodePanelOpen = useAppStore((state) => state.isCodePanelOpen)
  const toggleCodePanel = useAppStore((state) => state.toggleCodePanel)
  const toggleTemplateModal = useAppStore((state) => state.toggleTemplateModal)
  const renameDiagram = useAppStore((state) => state.renameDiagram)
  const isCommentsPanelOpen = useAppStore((state) => state.isCommentsPanelOpen)
  const toggleCommentsPanel = useAppStore((state) => state.toggleCommentsPanel)
  const runValidation = useAppStore((state) => state.runValidation)
  const validationResults = useAppStore((state) => state.validationResults)
  const enterPresentation = useAppStore((state) => state.enterPresentation)

  const [name, setName] = useState(activeDiagram?.name ?? '')
  const [isValidationOpen, setIsValidationOpen] = useState(false)

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

  function handleValidate(): void {
    runValidation()
    setIsValidationOpen(true)
  }

  return (
    <>
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
          style={{ ...buttonBase, background: isDocsPanelOpen ? '#2f81f7' : '#21262d' }}
        >
          📝 Docs
        </button>
        <button
          type="button"
          onClick={toggleCodePanel}
          style={{ ...buttonBase, background: isCodePanelOpen ? '#2f81f7' : '#21262d' }}
        >
          💻 Code
        </button>
        <button
          type="button"
          onClick={toggleTemplateModal}
          style={{ ...buttonBase, background: '#21262d' }}
        >
          📋 Templates
        </button>
        <button
          type="button"
          onClick={toggleCommentsPanel}
          style={{ ...buttonBase, background: isCommentsPanelOpen ? '#2f81f7' : '#21262d' }}
        >
          💬 Comentários
        </button>
        <button
          type="button"
          onClick={handleValidate}
          style={{ ...buttonBase, background: '#21262d' }}
        >
          🔍 Validar
        </button>
        <button
          type="button"
          onClick={enterPresentation}
          style={{ ...buttonBase, background: '#21262d' }}
        >
          ▶️ Apresentar
        </button>
        <ExportMenu />
      </div>
      {isValidationOpen ? (
        <ValidationModal
          results={validationResults}
          onClose={() => setIsValidationOpen(false)}
        />
      ) : null}
    </>
  )
}
