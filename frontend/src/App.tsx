import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'

import Home from './pages/Home'
import DiagramPage from './pages/Diagram'
import NotFound from './pages/NotFound'
import { useAppStore } from './store/useAppStore'

export default function App() {
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
