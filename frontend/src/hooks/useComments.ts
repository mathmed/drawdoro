import { useEffect, useMemo } from 'react'

import type { Comment } from '../api/types'
import { useAppStore } from '../store/useAppStore'

interface UseCommentsResult {
  comments: Comment[]
  addComment: (content: string) => Promise<void>
}

// Reads comments from the shared store (single source of truth so the badges and
// the panel stay in sync) and exposes the subset for a given element.
export function useComments(diagramId: string | null, elementId: string | null): UseCommentsResult {
  const allComments = useAppStore((state) => state.comments)
  const loadComments = useAppStore((state) => state.loadComments)
  const addCommentToStore = useAppStore((state) => state.addComment)

  useEffect(() => {
    if (diagramId !== null) {
      void loadComments(diagramId)
    }
  }, [diagramId, loadComments])

  const comments = useMemo(() => {
    if (elementId === null) {
      return allComments
    }
    return allComments.filter((comment) => comment.element_id === elementId)
  }, [allComments, elementId])

  async function addComment(content: string): Promise<void> {
    if (elementId === null) {
      return
    }
    await addCommentToStore(elementId, content)
  }

  return { comments, addComment }
}
