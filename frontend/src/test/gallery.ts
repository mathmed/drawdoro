import type { GalleryItemSummary } from '../api/types'

export function galleryItem(values: Partial<GalleryItemSummary> = {}): GalleryItemSummary {
  return {
    id: 'item-1',
    name: 'Load balancer',
    kind: 'shapes',
    tags: [],
    description: null,
    image_mime_type: null,
    thumbnail_base64: null,
    width: 200,
    height: 100,
    size_bytes: 1024,
    created_at: '2026-10-01T10:00:00Z',
    updated_at: '2026-10-01T10:00:00Z',
    ...values,
  }
}
