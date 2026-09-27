import { useAppStore } from '../../store/useAppStore'
import DrawingCanvas from '../canvas/DrawingCanvas'
import CodePanel from '../code/CodePanel'
import CommentsPanel from '../comments/CommentsPanel'
import PresentationMode from '../presentation/PresentationMode'
import Sidebar from '../sidebar/Sidebar'
import TemplateModal from '../templates/TemplateModal'
import Toolbar from '../toolbar/Toolbar'
import RightPanel from './RightPanel'

export default function AppLayout() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isDocsPanelOpen = useAppStore((state) => state.isDocsPanelOpen)
  const isCodePanelOpen = useAppStore((state) => state.isCodePanelOpen)
  const isTemplateModalOpen = useAppStore((state) => state.isTemplateModalOpen)
  const isCommentsPanelOpen = useAppStore((state) => state.isCommentsPanelOpen)
  const isPresentationMode = useAppStore((state) => state.isPresentationMode)

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
      {isPresentationMode ? null : <Sidebar />}
      <main style={{ flex: 1, position: 'relative', minWidth: 0 }}>
        {activeDiagram !== null ? (
          <>
            <DrawingCanvas key={activeDiagram.id} diagram={activeDiagram} />
            {isPresentationMode ? null : <Toolbar />}
            {!isPresentationMode && isCodePanelOpen ? <CodePanel /> : null}
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
      {activeDiagram !== null && !isPresentationMode && isDocsPanelOpen ? <RightPanel /> : null}
      {activeDiagram !== null && !isPresentationMode && isCommentsPanelOpen ? (
        <CommentsPanel />
      ) : null}
      {activeDiagram !== null && !isPresentationMode && isTemplateModalOpen ? (
        <TemplateModal />
      ) : null}
      {isPresentationMode ? <PresentationMode /> : null}
    </div>
  )
}
