import { useEffect } from 'react'
import { useParams } from 'react-router-dom'

import AppLayout from '../components/layout/AppLayout'
import { useAppStore } from '../store/useAppStore'

export default function DiagramPage() {
  const { id } = useParams<{ id: string }>()
  const loadDiagram = useAppStore((state) => state.loadDiagram)

  useEffect(() => {
    if (id !== undefined) {
      void loadDiagram(id)
    }
  }, [id, loadDiagram])

  return <AppLayout />
}
