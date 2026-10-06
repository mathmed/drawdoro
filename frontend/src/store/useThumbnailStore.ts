import type { Editor } from 'tldraw'
import { create } from 'zustand'

import { listDiagramThumbnails, saveDiagramThumbnail } from '../api/diagrams'
import type { ThumbnailTheme } from '../api/types'
import { renderDiagramThumbnails, type RenderedImage } from '../utils/diagramThumbnail'
import { isOlder } from '../utils/freshness'

export interface Thumbnail {
  // A data URL, or null when the diagram has nothing to show.
  src: string | null
  // The diagram's updated_at the preview was rendered from.
  version: string
}

export interface ProjectThumbnails {
  // False until the project's previews were fetched once in this theme.
  loaded: boolean
  items: Record<string, Thumbnail>
}

export interface ThumbnailTarget {
  projectId: string
  diagramId: string
  version: string
}

const THEMES: ThumbnailTheme[] = ['light', 'dark']
const EMPTY: ProjectThumbnails = { loaded: false, items: {} }

export function projectKey(theme: ThumbnailTheme, projectId: string): string {
  return `${theme}:${projectId}`
}

function dataUrl(image: RenderedImage | null): string | null {
  return image === null ? null : `data:${image.mimeType};base64,${image.base64}`
}

interface ThumbnailState {
  byProject: Record<string, ProjectThumbnails>
  load: (projectId: string, theme: ThumbnailTheme) => Promise<void>
  // Whether the preview of this diagram version is missing or older; unknown counts as missing.
  needsRefresh: (target: ThumbnailTarget) => boolean
  // Renders the editor's page and stores it as the preview of the target version.
  capture: (editor: Editor, target: ThumbnailTarget) => Promise<void>
}

export const useThumbnailStore = create<ThumbnailState>((set, get) => {
  function remember(target: ThumbnailTarget, images: Record<ThumbnailTheme, string | null>): void {
    const byProject = { ...get().byProject }
    for (const theme of THEMES) {
      const key = projectKey(theme, target.projectId)
      const current = byProject[key] ?? EMPTY
      byProject[key] = {
        ...current,
        items: { ...current.items, [target.diagramId]: { src: images[theme], version: target.version } },
      }
    }
    set({ byProject })
  }

  return {
    byProject: {},

    load: async (projectId, theme) => {
      const key = projectKey(theme, projectId)
      try {
        const listed = await listDiagramThumbnails(projectId, theme)
        const items: Record<string, Thumbnail> = {}
        for (const thumbnail of listed) {
          items[thumbnail.diagram_id] = {
            src: `data:${thumbnail.mime_type};base64,${thumbnail.image_base64}`,
            version: thumbnail.version,
          }
        }
        // A preview this tab stored while the request was in flight is newer than the listed one.
        const previous = get().byProject[key]?.items ?? {}
        for (const [diagramId, thumbnail] of Object.entries(previous)) {
          const fetched = items[diagramId]
          if (fetched !== undefined && isOlder(fetched.version, thumbnail.version)) {
            items[diagramId] = thumbnail
          }
        }
        set({ byProject: { ...get().byProject, [key]: { loaded: true, items } } })
      } catch {
        // Cards fall back to their placeholder; the next visit tries again.
        const current = get().byProject[key] ?? EMPTY
        set({ byProject: { ...get().byProject, [key]: { ...current, loaded: true } } })
      }
    },

    needsRefresh: ({ projectId, diagramId, version }) => {
      for (const theme of THEMES) {
        const known = get().byProject[projectKey(theme, projectId)]?.items[diagramId]
        if (known !== undefined && !isOlder(known.version, version)) {
          return false
        }
      }
      return true
    },

    capture: async (editor, target) => {
      try {
        const { light, dark } = await renderDiagramThumbnails(editor)
        await saveDiagramThumbnail(target.diagramId, {
          version: target.version,
          light_base64: light?.base64 ?? null,
          dark_base64: dark?.base64 ?? null,
        })
        remember(target, { light: dataUrl(light), dark: dataUrl(dark) })
      } catch {
        // A missing preview is not worth bothering the user: the card keeps its previous one or the
        // placeholder, and the next change or visit renders it again.
      }
    },
  }
})
