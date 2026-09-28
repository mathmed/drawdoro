import { Loader2 } from 'lucide-react'

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
import Inspector from './Inspector'

export default function AppLayout() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const isLoadingDiagram = useAppStore((state) => state.isLoadingDiagram)
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

  function renderStage() {
    if (hasDiagram) {
      return <DrawingCanvas key={activeDiagram.id} diagram={activeDiagram} />
    }
    if (isLoadingDiagram) {
      return (
        <div className="full-center">
          <Loader2 size={16} className="spinner" /> Opening diagram…
        </div>
      )
    }
    return <HomeView />
  }

  return (
    <div className="app">
      {showChrome && isSidebarOpen ? <Sidebar /> : null}
      <div className="main">
        {showChrome ? <TopBar /> : null}
        <div className="stage-area">
          <div className="stage">{renderStage()}</div>
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
