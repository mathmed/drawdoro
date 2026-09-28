import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'

import DialogHost from './components/ui/DialogHost'
import Toaster from './components/ui/Toaster'
import DiagramPage from './pages/Diagram'
import Home from './pages/Home'
import NotFound from './pages/NotFound'
import { useAppStore } from './store/useAppStore'

export default function App() {
  const loadWorkspaces = useAppStore((state) => state.loadWorkspaces)

  useEffect(() => {
    void loadWorkspaces()
  }, [loadWorkspaces])

  return (
    <>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/diagrams/:id" element={<DiagramPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <DialogHost />
      <Toaster />
    </>
  )
}
