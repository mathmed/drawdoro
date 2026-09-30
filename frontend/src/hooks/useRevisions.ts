import { useCallback, useEffect, useRef, useState } from 'react'
import { loadSnapshot, type TLStoreSnapshot } from 'tldraw'

import { listRevisions, restoreRevision } from '../api/revisions'
import type { DiagramRevision } from '../api/types'
import { useAppStore } from '../store/useAppStore'

// Saves land every few seconds while someone edits; the list refreshes once they settle.
const REFRESH_DELAY_MS = 1500

interface UseRevisionsResult {
  revisions: DiagramRevision[]
  isLoading: boolean
  restore: (revision: DiagramRevision) => Promise<void>
}

export function useRevisions(diagramId: string | null): UseRevisionsResult {
  const updatedAt = useAppStore((state) => state.activeDiagram?.updated_at)
  const [revisions, setRevisions] = useState<DiagramRevision[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const request = useRef(0)

  const refresh = useCallback(async () => {
    if (diagramId === null) {
      return
    }
    const current = ++request.current
    try {
      const loaded = await listRevisions(diagramId)
      if (current === request.current) {
        setRevisions(loaded)
      }
    } finally {
      if (current === request.current) {
        setIsLoading(false)
      }
    }
  }, [diagramId])

  useEffect(() => {
    setIsLoading(true)
    setRevisions([])
    void refresh()
  }, [refresh])

  useEffect(() => {
    const timer = setTimeout(() => void refresh(), REFRESH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [updatedAt, refresh])

  const restore = useCallback(
    async (revision: DiagramRevision) => {
      if (diagramId === null) {
        return
      }
      const restored = await restoreRevision(diagramId, revision.id)
      // Other editors get it over the realtime socket; this tab draws it right away as well.
      const { applyPushedDiagram, editor } = useAppStore.getState()
      if (applyPushedDiagram(restored) && editor !== null && restored.canvas_state !== null) {
        editor.store.mergeRemoteChanges(() => {
          loadSnapshot(editor.store, restored.canvas_state as unknown as TLStoreSnapshot)
        })
      }
      await refresh()
    },
    [diagramId, refresh],
  )

  return { revisions, isLoading, restore }
}
