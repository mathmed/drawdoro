import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'

import DialogHost from './components/ui/DialogHost'
import Toaster from './components/ui/Toaster'
import AuthCallback from './pages/AuthCallback'
import DiagramPage from './pages/Diagram'
import Home from './pages/Home'
import Landing from './pages/Landing'
import NotFound from './pages/NotFound'
import RenderDiagramPage from './pages/RenderDiagram'
import SharedDiagramPage from './pages/SharedDiagram'
import { useAppStore } from './store/useAppStore'
import { useAuthStore } from './store/useAuthStore'

function SignedInApp() {
  const loadWorkspaces = useAppStore((state) => state.loadWorkspaces)

  useEffect(() => {
    void loadWorkspaces()
  }, [loadWorkspaces])

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/diagrams/:id" element={<DiagramPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

// Any route shows the landing page until the user signs in, then renders the app.
function AuthGate() {
  const status = useAuthStore((state) => state.status)

  if (status === 'loading') {
    return (
      <div className="full-center">
        <Loader2 size={16} className="spinner" />
      </div>
    )
  }
  return status === 'signed-in' ? <SignedInApp /> : <Landing />
}

export default function App() {
  const initialize = useAuthStore((state) => state.initialize)

  useEffect(() => {
    void initialize()
  }, [initialize])

  return (
    <>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        {/* Public: the share link works signed-in or as a guest, so it sits outside the AuthGate. */}
        <Route path="/share/:token" element={<SharedDiagramPage />} />
        {/* Public too: the MCP server's headless browser hands it a canvas to export as PNG. */}
        <Route path="/render" element={<RenderDiagramPage />} />
        <Route path="*" element={<AuthGate />} />
      </Routes>
      <DialogHost />
      <Toaster />
    </>
  )
}
