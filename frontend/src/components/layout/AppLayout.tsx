import { useAppStore } from '../../store/useAppStore'
import DrawingCanvas from '../canvas/DrawingCanvas'
import CodePanel from '../code/CodePanel'
import DocsPanel from '../docs/DocsPanel'
import Sidebar from '../sidebar/Sidebar'
import TemplateModal from '../templates/TemplateModal'
import Toolbar from '../toolbar/Toolbar'

export default function AppLayout() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isDocsPanelOpen = useAppStore((state) => state.isDocsPanelOpen)
  const isCodePanelOpen = useAppStore((state) => state.isCodePanelOpen)
  const isTemplateModalOpen = useAppStore((state) => state.isTemplateModalOpen)

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        background: '#0f1117',
        color: '#e6edf3',
      }}
    >
      <Sidebar />
      <main style={{ flex: 1, position: 'relative', minWidth: 0 }}>
        {activeDiagram !== null ? (
          <>
            <DrawingCanvas key={activeDiagram.id} diagram={activeDiagram} />
            <Toolbar />
            {isCodePanelOpen ? <CodePanel /> : null}
          </>
        ) : (
          <div
            style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              opacity: 0.7,
            }}
          >
            <div style={{ fontSize: 40 }}>🗺️</div>
            <div style={{ fontSize: 15 }}>Select or create a diagram to start drawing.</div>
          </div>
        )}
      </main>
      {activeDiagram !== null && isDocsPanelOpen ? <DocsPanel /> : null}
      {activeDiagram !== null && isTemplateModalOpen ? <TemplateModal /> : null}
    </div>
  )
}
