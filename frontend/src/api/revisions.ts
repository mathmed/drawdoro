import apiClient from './client'
import type { Diagram, DiagramRevision, DiagramRevisionDetail } from './types'

export async function listRevisions(diagramId: string): Promise<DiagramRevision[]> {
  const { data } = await apiClient.get<DiagramRevision[]>(`/diagrams/${diagramId}/revisions`)
  return data
}

export async function getRevision(diagramId: string, revisionId: string): Promise<DiagramRevisionDetail> {
  const { data } = await apiClient.get<DiagramRevisionDetail>(`/diagrams/${diagramId}/revisions/${revisionId}`)
  return data
}

export async function restoreRevision(diagramId: string, revisionId: string): Promise<Diagram> {
  const { data } = await apiClient.post<Diagram>(`/diagrams/${diagramId}/revisions/${revisionId}/restore`)
  return data
}
