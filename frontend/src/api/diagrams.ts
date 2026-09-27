import apiClient from './client'
import type { CanvasState, Diagram, SemanticMetadata } from './types'

export interface UpdateDiagramInput {
  name: string
  folder_id: string | null
  canvas_state: CanvasState | null
  mermaid_source: string | null
  d2_source: string | null
  semantic_metadata?: SemanticMetadata | null
}

export async function listDiagrams(projectId: string, folderId?: string): Promise<Diagram[]> {
  const { data } = await apiClient.get<Diagram[]>(`/projects/${projectId}/diagrams`)
  if (folderId === undefined) {
    return data
  }
  return data.filter((diagram) => diagram.folder_id === folderId)
}

export async function createDiagram(
  projectId: string,
  name: string,
  folderId?: string,
): Promise<Diagram> {
  const { data } = await apiClient.post<Diagram>(`/projects/${projectId}/diagrams`, {
    name,
    folder_id: folderId ?? null,
  })
  return data
}

export async function getDiagram(projectId: string, diagramId: string): Promise<Diagram> {
  const { data } = await apiClient.get<Diagram>(`/projects/${projectId}/diagrams/${diagramId}`)
  return data
}

// The backend PUT replaces every field, so callers must send the full desired state
// (not just the canvas) to avoid wiping name, folder or the alternative sources.
export async function updateDiagram(
  projectId: string,
  diagramId: string,
  input: UpdateDiagramInput,
): Promise<Diagram> {
  const { data } = await apiClient.put<Diagram>(
    `/projects/${projectId}/diagrams/${diagramId}`,
    input,
  )
  return data
}
