import apiClient from './client'
import type { Comment, CommentStatus } from './types'

export async function listComments(diagramId: string, status: CommentStatus = 'all'): Promise<Comment[]> {
  const { data } = await apiClient.get<Comment[]>(`/diagrams/${diagramId}/comments`, { params: { status } })
  return data
}

export async function createComment(
  diagramId: string,
  elementId: string | null,
  content: string,
  authorId?: string,
): Promise<Comment> {
  const { data } = await apiClient.post<Comment>(`/diagrams/${diagramId}/comments`, {
    element_id: elementId,
    content,
    author_id: authorId ?? null,
  })
  return data
}

export async function setCommentResolved(diagramId: string, commentId: string, resolved: boolean): Promise<Comment> {
  const { data } = await apiClient.patch<Comment>(`/diagrams/${diagramId}/comments/${commentId}`, { resolved })
  return data
}
