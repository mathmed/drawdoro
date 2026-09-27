export type CanvasState = Record<string, unknown>
export type SemanticMetadata = Record<string, unknown>

export interface Workspace {
  id: string
  name: string
  slug: string
  created_at: string
  updated_at?: string
}

export interface Project {
  id: string
  workspace_id: string
  name: string
  description: string | null
  created_at: string
  updated_at?: string
}

export interface Folder {
  id: string
  project_id: string
  parent_folder_id: string | null
  name: string
  created_at?: string
  updated_at?: string
}

export interface Diagram {
  id: string
  project_id: string
  folder_id: string | null
  name: string
  canvas_state: CanvasState | null
  mermaid_source: string | null
  d2_source: string | null
  semantic_metadata?: SemanticMetadata | null
  created_at?: string
  updated_at?: string
}

export interface DocumentationPage {
  id: string
  diagram_id: string
  content: string
  created_at?: string
  updated_at?: string
}
