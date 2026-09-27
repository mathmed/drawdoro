import { Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import DiagramPage from './pages/Diagram'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/diagrams/:id" element={<DiagramPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
