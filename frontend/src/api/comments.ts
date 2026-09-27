import apiClient from './client'
import type { Comment } from './types'

export async function listComments(diagramId: string): Promise<Comment[]> {
  const { data } = await apiClient.get<Comment[]>(`/diagrams/${diagramId}/comments`)
  return data
}

export async function createComment(
  diagramId: string,
  elementId: string,
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
