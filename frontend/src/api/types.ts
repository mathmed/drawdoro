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
  semantic_metadata?: SemanticMetadata | null
  created_at?: string
  updated_at?: string
}

// Pushed over the realtime socket to open editors after every saved change to a diagram.
export type PushedDiagram = Pick<
  Diagram,
  'id' | 'name' | 'folder_id' | 'canvas_state' | 'semantic_metadata' | 'updated_at'
>

export interface DocumentationPage {
  id: string
  diagram_id: string
  content: string
  created_at?: string
  updated_at?: string
}

export interface Comment {
  id: string
  diagram_id: string
  element_id: string
  content: string
  author_id: string | null
  author_name: string | null
  created_at: string
}

export type SemanticType =
  | 'service'
  | 'database'
  | 'queue'
  | 'gateway'
  | 'client'
  | 'cache'
  | 'external'
  | 'custom'

export interface ShapeMetadata {
  type?: SemanticType
  label?: string
  technology?: string
  notes?: string
}

export interface ValidationResult {
  severity: 'error' | 'warning'
  message: string
  shapeIds: string[]
}

export type WorkspaceRole = 'owner' | 'editor' | 'viewer'

export interface WorkspaceMember {
  user_id: string
  name: string
  email: string
  role: WorkspaceRole
}

export type GalleryItemKind = 'shapes' | 'image'

export interface GalleryItemSummary {
  id: string
  name: string
  kind: GalleryItemKind
  image_mime_type: string | null
  // Base64 PNG preview rendered by the client when the item was saved.
  thumbnail_base64: string | null
  created_at: string
  updated_at: string
}

export interface GalleryItem extends GalleryItemSummary {
  // tldraw content (shapes, bindings, assets) for "shapes" items.
  content: Record<string, unknown> | null
  image_base64: string | null
}

export interface CreateGalleryItemInput {
  name: string
  kind: GalleryItemKind
  content?: Record<string, unknown>
  image_base64?: string
  thumbnail_base64?: string | null
}
