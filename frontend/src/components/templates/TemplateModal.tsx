import { BUILTIN_TEMPLATES, type BuiltinTemplate } from '../../data/templates'
import { useAppStore } from '../../store/useAppStore'

export default function TemplateModal() {
  const toggleTemplateModal = useAppStore((state) => state.toggleTemplateModal)
  const setCodeLanguage = useAppStore((state) => state.setCodeLanguage)
  const saveMermaidSource = useAppStore((state) => state.saveMermaidSource)
  const isCodePanelOpen = useAppStore((state) => state.isCodePanelOpen)
  const toggleCodePanel = useAppStore((state) => state.toggleCodePanel)

  async function applyTemplate(template: BuiltinTemplate): Promise<void> {
    setCodeLanguage('mermaid')
    await saveMermaidSource(template.mermaid)
    if (!isCodePanelOpen) {
      toggleCodePanel()
    }
    toggleTemplateModal()
  }

  return (
    <div
      onClick={toggleTemplateModal}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 500,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <div
        onClick={(event) => event.stopPropagation()}
        style={{
          width: 'min(920px, 100%)',
          maxHeight: '80vh',
          overflow: 'auto',
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: 12,
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        }}
      >
        <header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 18px',
            borderBottom: '1px solid #30363d',
            position: 'sticky',
            top: 0,
            background: '#161b22',
          }}
        >
          <span style={{ fontSize: 15, fontWeight: 600 }}>📋 Templates</span>
          <button
            type="button"
            onClick={toggleTemplateModal}
            style={{
              background: 'transparent',
              color: '#8b949e',
              border: 'none',
              cursor: 'pointer',
              fontSize: 16,
            }}
          >
            ✕
          </button>
        </header>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: 14,
            padding: 18,
          }}
        >
          {BUILTIN_TEMPLATES.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() => void applyTemplate(template)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'stretch',
                textAlign: 'left',
                gap: 8,
                background: '#0f1117',
                border: '1px solid #30363d',
                borderRadius: 10,
                padding: 14,
                cursor: 'pointer',
                color: '#e6edf3',
              }}
            >
              <span style={{ fontSize: 14, fontWeight: 600 }}>{template.name}</span>
              <span style={{ fontSize: 12, color: '#8b949e', lineHeight: 1.4 }}>
                {template.description}
              </span>
              <pre
                style={{
                  margin: 0,
                  padding: 10,
                  background: '#010409',
                  border: '1px solid #30363d',
                  borderRadius: 8,
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                  fontSize: 10,
                  lineHeight: 1.4,
                  color: '#8b949e',
                  maxHeight: 130,
                  overflow: 'hidden',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {template.mermaid}
              </pre>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
