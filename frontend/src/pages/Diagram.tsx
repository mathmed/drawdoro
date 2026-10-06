import { FileQuestion, RotateCw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import AppLayout from '../components/layout/AppLayout'
import EmptyState from '../components/ui/EmptyState'
import { useAppStore } from '../store/useAppStore'

export default function DiagramPage() {
  const { id } = useParams<{ id: string }>()
  const loadDiagram = useAppStore((state) => state.loadDiagram)
  // Bumped by "Try again"; the store only applies the latest attempt.
  const [attempt, setAttempt] = useState(0)
  const retry = useCallback(() => setAttempt((count) => count + 1), [])
  // The attempt whose load has finished; until then the stage shows the opening loader.
  const [settledAttempt, setSettledAttempt] = useState<string | null>(null)
  const attemptKey = `${id}:${attempt}`
  // The attempt that found no diagram; a new one (navigation or "Try again") clears it.
  const [missingAttempt, setMissingAttempt] = useState<string | null>(null)
  const notFound = missingAttempt === attemptKey

  useEffect(() => {
    if (id === undefined) {
      return
    }
    // A later navigation supersedes this load; its outcome must not mark the new diagram missing.
    let isCurrent = true
    void loadDiagram(id).then(() => {
      if (!isCurrent) {
        return
      }
      setSettledAttempt(`${id}:${attempt}`)
      if (useAppStore.getState().activeDiagram?.id !== id) {
        setMissingAttempt(`${id}:${attempt}`)
      }
    })
    return () => {
      isCurrent = false
    }
  }, [id, attempt, loadDiagram])

  if (notFound) {
    return (
      <div className="full-center">
        <EmptyState
          icon={<FileQuestion size={20} />}
          title="Diagram not found"
          description="It may have been deleted, or the link is wrong."
          action={
            <div className="empty-state-actions">
              <button type="button" className="btn btn-secondary" onClick={retry}>
                <RotateCw size={14} /> Try again
              </button>
              <Link to="/" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
                Back to overview
              </Link>
            </div>
          }
        />
      </div>
    )
  }

  return <AppLayout isOpeningDiagram={settledAttempt !== attemptKey} onRetryDiagram={retry} />
}
