import { useEffect } from 'react'
import type { Editor } from 'tldraw'

import { authConfig } from '../auth/config'
import { useAppStore } from '../store/useAppStore'
import { useThumbnailStore } from '../store/useThumbnailStore'
import { canStoreThumbnail } from '../utils/diagramThumbnail'

// Long enough after the last edit or saved version that a burst of changes renders once.
export const THUMBNAIL_REFRESH_DELAY_MS = 2000

// Keeps the listing preview of the open diagram up to date: after every saved version (this tab's,
// another editor's or an agent's) and on open when the stored one is missing or older. Only people
// who can edit store previews.
export function useDiagramThumbnail(editor: Editor | null): void {
  const diagramId = useAppStore((state) => state.activeDiagram?.id)
  const projectId = useAppStore((state) => state.activeDiagram?.project_id)
  const version = useAppStore((state) => state.activeDiagram?.updated_at)
  const canStore = useAppStore((state) => canStoreThumbnail(state.myRole, authConfig.enabled))

  useEffect(() => {
    if (editor === null || !canStore || diagramId === undefined || projectId === undefined || version === undefined) {
      return
    }
    const target = { projectId, diagramId, version }
    const { needsRefresh, capture } = useThumbnailStore.getState()
    if (!needsRefresh(target)) {
      return
    }
    let timer: ReturnType<typeof setTimeout> | undefined
    function schedule(): void {
      clearTimeout(timer)
      timer = setTimeout(() => {
        if (editor !== null && !editor.getIsReadonly()) {
          void capture(editor, target)
        }
      }, THUMBNAIL_REFRESH_DELAY_MS)
    }
    schedule()
    // Local edits push the render back, so it never runs mid-gesture; their save brings a newer version.
    const unlisten = editor.store.listen(schedule, { scope: 'document', source: 'user' })
    return () => {
      clearTimeout(timer)
      unlisten()
    }
  }, [editor, canStore, diagramId, projectId, version])
}
