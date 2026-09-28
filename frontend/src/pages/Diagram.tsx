import { FileQuestion } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import AppLayout from '../components/layout/AppLayout'
import EmptyState from '../components/ui/EmptyState'
import { useAppStore } from '../store/useAppStore'

export default function DiagramPage() {
  const { id } = useParams<{ id: string }>()
  const loadDiagram = useAppStore((state) => state.loadDiagram)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (id === undefined) {
      return
    }
    setNotFound(false)
    void loadDiagram(id).then(() => {
      if (useAppStore.getState().activeDiagram?.id !== id) {
        setNotFound(true)
      }
    })
  }, [id, loadDiagram])

  if (notFound) {
    return (
      <div className="full-center">
        <EmptyState
          icon={<FileQuestion size={20} />}
          title="Diagram not found"
          description="It may have been deleted, or the link is wrong."
          action={
            <Link to="/" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
              Back to overview
            </Link>
          }
        />
      </div>
    )
  }

  return <AppLayout />
}
