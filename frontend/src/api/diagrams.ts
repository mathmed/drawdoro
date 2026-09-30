import apiClient from './client'
import { TAB_CLIENT_ID } from './tabClientId'
import type { CanvasState, Diagram, DiagramSummary, SemanticMetadata } from './types'

export interface UpdateDiagramInput {
  name: string
  folder_id: string | null
  canvas_state: CanvasState | null
  semantic_metadata?: SemanticMetadata | null
}

export function toSummary(diagram: DiagramSummary): DiagramSummary {
  const { id, project_id, folder_id, name, created_at, updated_at } = diagram
  return { id, project_id, folder_id, name, created_at, updated_at }
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

// Links carry only the diagram id; the response says which project it belongs to.
export async function getDiagramById(diagramId: string): Promise<Diagram> {
  const { data } = await apiClient.get<Diagram>(`/diagrams/${diagramId}`)
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
    { headers: { 'X-Client-Id': TAB_CLIENT_ID } },
  )
  return data
}

export async function deleteDiagram(projectId: string, diagramId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/diagrams/${diagramId}`)
}

export async function shareDiagram(diagramId: string): Promise<string> {
  const { data } = await apiClient.post<{ share_token: string }>(`/diagrams/${diagramId}/share`)
  return data.share_token
}

export interface SharedDiagram {
  id: string
  name: string
  canvas_state: CanvasState | null
  semantic_metadata?: SemanticMetadata | null
}

// Public: no auth required. Used by the shareable link and by guest visitors.
export async function getSharedDiagram(shareToken: string): Promise<SharedDiagram> {
  const { data } = await apiClient.get<SharedDiagram>(`/share/${shareToken}`)
  return data
}
