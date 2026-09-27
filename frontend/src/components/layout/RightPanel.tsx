import { useAppStore } from '../../store/useAppStore'
import AdrPanel from '../adr/AdrPanel'
import DocsPanel from '../docs/DocsPanel'
import SemanticPanel from '../semantic/SemanticPanel'

const TABS = [
  { id: 'docs', label: '📝 Docs' },
  { id: 'adrs', label: '📋 ADRs' },
  { id: 'info', label: '🏷️ Info' },
] as const

export default function RightPanel() {
  const rightPanelTab = useAppStore((state) => state.rightPanelTab)
  const setRightPanelTab = useAppStore((state) => state.setRightPanelTab)
  const toggleDocsPanel = useAppStore((state) => state.toggleDocsPanel)

  return (
    <aside
      style={{
        width: 340,
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
          padding: '6px 8px',
          borderBottom: '1px solid #30363d',
          gap: 6,
        }}
      >
        <div style={{ display: 'flex', gap: 4 }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setRightPanelTab(tab.id)}
              style={{
                background: rightPanelTab === tab.id ? '#2f81f7' : '#21262d',
                color: '#e6edf3',
                border: '1px solid #30363d',
                borderRadius: 6,
                padding: '5px 8px',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
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
      {rightPanelTab === 'docs' ? <DocsPanel /> : null}
      {rightPanelTab === 'adrs' ? <AdrPanel /> : null}
      {rightPanelTab === 'info' ? <SemanticPanel /> : null}
    </aside>
  )
}
