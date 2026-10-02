import { useDelayedVisibility } from '../../hooks/useDelayedVisibility'
import { useGlobalShortcuts } from '../../hooks/useGlobalShortcuts'
import { useAppStore } from '../../store/useAppStore'
import DrawingCanvas from '../canvas/DrawingCanvas'
import NewDiagramDialog from '../diagram/NewDiagramDialog'
import HomeView from '../home/HomeView'
import CommandPalette from '../palette/CommandPalette'
import PresentationMode from '../presentation/PresentationMode'
import ValidationModal from '../semantic/ValidationModal'
import Sidebar from '../sidebar/Sidebar'
import TopBar from '../topbar/TopBar'
import BrandLoader from '../ui/loading/BrandLoader'
import LoadingOverlay from '../ui/loading/LoadingOverlay'
import TopProgressBar from '../ui/loading/TopProgressBar'
import Inspector from './Inspector'

interface AppLayoutProps {
  // Set by a diagram route until its load settles, so the overview never flashes before the canvas.
  isOpeningDiagram?: boolean
  onRetryDiagram?: () => void
}

export default function AppLayout({ isOpeningDiagram = false, onRetryDiagram }: AppLayoutProps) {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isLoadingDiagram = useAppStore((state) => state.isLoadingDiagram)
  const isRefreshingProject = useAppStore((state) => state.isLoadingProject && state.diagrams.length > 0)
  const isSidebarOpen = useAppStore((state) => state.isSidebarOpen)
  const isInspectorOpen = useAppStore((state) => state.isInspectorOpen)
  const isCommandPaletteOpen = useAppStore((state) => state.isCommandPaletteOpen)
  const isValidationOpen = useAppStore((state) => state.isValidationOpen)
  const validationResults = useAppStore((state) => state.validationResults)
  const closeValidation = useAppStore((state) => state.closeValidation)
  const newDiagramDialog = useAppStore((state) => state.newDiagramDialog)
  const isPresentationMode = useAppStore((state) => state.isPresentationMode)

  useGlobalShortcuts()

  const hasDiagram = activeDiagram !== null
  const showChrome = !isPresentationMode
  const isOpening = !hasDiagram && (isLoadingDiagram || isOpeningDiagram)
  // The canvas mounts as soon as the diagram arrives and the loader fades out over it.
  const showOpeningLoader = useDelayedVisibility(isOpening)
  // Switching diagrams or refreshing a project keeps the current content on screen.
  const isWorkingInBackground = hasDiagram ? isLoadingDiagram : isRefreshingProject

  function renderStage() {
    if (hasDiagram) {
      return <DrawingCanvas key={activeDiagram.id} diagram={activeDiagram} />
    }
    if (isOpening) {
      return null
    }
    return <HomeView />
  }

  return (
    <div className="app">
      {showChrome && isSidebarOpen ? <Sidebar /> : null}
      <div className="main">
        {showChrome ? <TopBar /> : null}
        <div className="stage-area">
          <div className="stage" aria-busy={isOpening}>
            {renderStage()}
            <TopProgressBar active={isWorkingInBackground} label={hasDiagram ? 'Opening diagram' : 'Refreshing project'} />
            <LoadingOverlay visible={showOpeningLoader}>
              <BrandLoader label="Opening diagram" onRetry={onRetryDiagram} />
            </LoadingOverlay>
          </div>
        </div>
      </div>
      {showChrome && hasDiagram && isInspectorOpen ? <Inspector /> : null}

      {isValidationOpen ? <ValidationModal results={validationResults} onClose={closeValidation} /> : null}
      {newDiagramDialog !== null ? <NewDiagramDialog initialFolderId={newDiagramDialog.folderId} /> : null}
      {isCommandPaletteOpen ? <CommandPalette /> : null}
      {isPresentationMode ? <PresentationMode /> : null}
    </div>
  )
}
