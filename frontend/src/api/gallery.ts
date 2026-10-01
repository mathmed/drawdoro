import apiClient from './client'
import type { CreateGalleryItemInput, GalleryItem, GalleryItemChanges, GalleryItemSummary } from './types'

export async function listGalleryItems(): Promise<GalleryItemSummary[]> {
  const { data } = await apiClient.get<GalleryItemSummary[]>('/gallery')
  return data
}

export async function getGalleryItem(itemId: string): Promise<GalleryItem> {
  const { data } = await apiClient.get<GalleryItem>(`/gallery/${itemId}`)
  return data
}

export async function createGalleryItem(input: CreateGalleryItemInput): Promise<GalleryItem> {
  const { data } = await apiClient.post<GalleryItem>('/gallery', input)
  return data
}

export async function updateGalleryItem(itemId: string, changes: GalleryItemChanges): Promise<GalleryItemSummary> {
  const { data } = await apiClient.patch<GalleryItemSummary>(`/gallery/${itemId}`, changes)
  return data
}

export async function deleteGalleryItem(itemId: string): Promise<void> {
  await apiClient.delete(`/gallery/${itemId}`)
}
