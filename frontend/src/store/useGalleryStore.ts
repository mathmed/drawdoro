import { create } from 'zustand'

import {
  createGalleryItem,
  deleteGalleryItem,
  getGalleryItem,
  listGalleryItems,
  updateGalleryItem,
} from '../api/gallery'
import type { CreateGalleryItemInput, GalleryItem, GalleryItemChanges, GalleryItemSummary } from '../api/types'

export type GalleryStatus = 'idle' | 'loading' | 'ready' | 'error'

interface GalleryState {
  items: GalleryItemSummary[]
  status: GalleryStatus
  // Full items (with their payload) already fetched, so inserting twice does not refetch.
  loadedItems: Record<string, GalleryItem>

  load: () => Promise<void>
  add: (input: CreateGalleryItemInput) => Promise<GalleryItem | null>
  fetchItem: (itemId: string) => Promise<GalleryItem | null>
  update: (itemId: string, changes: GalleryItemChanges) => Promise<boolean>
  remove: (itemId: string) => Promise<void>
}

function toSummary(item: GalleryItem): GalleryItemSummary {
  const { content: _content, image_base64: _image, ...summary } = item
  return summary
}

// Errors are reported by the API client's toast; the store only keeps the UI consistent.
export const useGalleryStore = create<GalleryState>((set, get) => ({
  items: [],
  status: 'idle',
  loadedItems: {},

  load: async () => {
    set({ status: 'loading' })
    try {
      set({ items: await listGalleryItems(), status: 'ready' })
    } catch {
      set({ status: 'error' })
    }
  },

  add: async (input) => {
    try {
      const item = await createGalleryItem(input)
      set({
        items: [toSummary(item), ...get().items],
        loadedItems: { ...get().loadedItems, [item.id]: item },
      })
      return item
    } catch {
      return null
    }
  },

  fetchItem: async (itemId) => {
    const cached = get().loadedItems[itemId]
    if (cached !== undefined) {
      return cached
    }
    try {
      const item = await getGalleryItem(itemId)
      set({ loadedItems: { ...get().loadedItems, [item.id]: item } })
      return item
    } catch {
      return null
    }
  },

  update: async (itemId, changes) => {
    try {
      const updated = await updateGalleryItem(itemId, changes)
      const cached = get().loadedItems[itemId]
      set({
        items: get().items.map((item) => (item.id === itemId ? updated : item)),
        loadedItems: cached === undefined ? get().loadedItems : { ...get().loadedItems, [itemId]: { ...cached, ...updated } },
      })
      return true
    } catch {
      // Already reported to the user.
      return false
    }
  },

  remove: async (itemId) => {
    try {
      await deleteGalleryItem(itemId)
      const { [itemId]: _removed, ...loadedItems } = get().loadedItems
      set({ items: get().items.filter((item) => item.id !== itemId), loadedItems })
    } catch {
      // Already reported to the user.
    }
  },
}))
