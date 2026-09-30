import type { Editor, TLContent, VecLike } from 'tldraw'

import type { GalleryItem } from '../api/types'
import { promptDialog } from '../store/useDialogStore'
import { useGalleryStore } from '../store/useGalleryStore'
import { toast } from '../store/useToastStore'

// dataTransfer type used when dragging a gallery tile onto the canvas.
export const GALLERY_DRAG_TYPE = 'application/x-gallery-item'
export const GALLERY_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

const THUMBNAIL_SIZE = 256

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1] ?? '')
    reader.onerror = () => reject(reader.error ?? new Error('Could not read the file'))
    reader.readAsDataURL(blob)
  })
}

function base64ToBlob(base64: string, type: string): Blob {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return new Blob([bytes], { type })
}

async function selectionThumbnail(editor: Editor): Promise<string | null> {
  const ids = editor.getSelectedShapeIds()
  const bounds = editor.getSelectionPageBounds()
  if (bounds === null) {
    return null
  }
  const scale = Math.min(1, THUMBNAIL_SIZE / Math.max(bounds.w, bounds.h, 1))
  try {
    const { blob } = await editor.toImage(ids, { format: 'png', background: false, scale, pixelRatio: 1, padding: 8 })
    return await blobToBase64(blob)
  } catch {
    // A missing preview is not worth failing the save.
    return null
  }
}

async function imageThumbnail(file: Blob): Promise<string | null> {
  const url = URL.createObjectURL(file)
  try {
    const image = new Image()
    image.src = url
    await image.decode()
    const scale = Math.min(1, THUMBNAIL_SIZE / Math.max(image.naturalWidth, image.naturalHeight, 1))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale))
    canvas.height = Math.max(1, Math.round(image.naturalHeight * scale))
    canvas.getContext('2d')?.drawImage(image, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
    return blob === null ? null : await blobToBase64(blob)
  } catch {
    return null
  } finally {
    URL.revokeObjectURL(url)
  }
}

export function canSaveSelection(editor: Editor | null): boolean {
  return editor !== null && editor.getSelectedShapeIds().length > 0
}

export async function saveSelectionToGallery(editor: Editor): Promise<void> {
  const ids = editor.getSelectedShapeIds()
  if (ids.length === 0) {
    toast('Select one or more shapes to save them to the gallery.', 'info')
    return
  }
  const name = await promptDialog({
    title: 'Save to gallery',
    description: 'Reuse this selection in any diagram from the Gallery tab.',
    label: 'Name',
    placeholder: 'e.g. Load balancer',
    confirmLabel: 'Save',
  })
  if (name === null) {
    return
  }
  // Inline asset data (e.g. pasted images) so the item does not depend on this diagram.
  const content = await editor.resolveAssetsInContent(editor.getContentFromCurrentPage(ids))
  if (content === undefined) {
    return
  }
  const thumbnail = await selectionThumbnail(editor)
  const saved = await useGalleryStore.getState().add({
    name,
    kind: 'shapes',
    content: content as unknown as Record<string, unknown>,
    thumbnail_base64: thumbnail,
  })
  if (saved !== null) {
    toast(`Saved “${saved.name}” to your gallery.`, 'success')
  }
}

export async function addImageToGallery(file: File): Promise<void> {
  if (!GALLERY_IMAGE_TYPES.includes(file.type)) {
    toast(`“${file.name}” is not a supported image. Use PNG, JPEG, GIF or WebP.`, 'error')
    return
  }
  const name = file.name.replace(/\.[^.]+$/, '') || 'Image'
  const [image, thumbnail] = await Promise.all([blobToBase64(file), imageThumbnail(file)])
  const saved = await useGalleryStore.getState().add({
    name,
    kind: 'image',
    image_base64: image,
    thumbnail_base64: thumbnail,
  })
  if (saved !== null) {
    toast(`Added “${saved.name}” to your gallery.`, 'success')
  }
}

function insertImage(editor: Editor, item: GalleryItem, point: VecLike): Promise<void> {
  const type = item.image_mime_type ?? 'image/png'
  const extension = type.split('/')[1] ?? 'png'
  const file = new File([base64ToBlob(item.image_base64 ?? '', type)], `${item.name}.${extension}`, { type })
  return editor.putExternalContent({ type: 'files', files: [file], point })
}

// Without a point the item lands in the middle of what the user is looking at.
export async function insertGalleryItem(editor: Editor, itemId: string, point?: VecLike): Promise<void> {
  if (editor.getIsReadonly()) {
    toast('You can only view this diagram.', 'info')
    return
  }
  const item = await useGalleryStore.getState().fetchItem(itemId)
  if (item === null) {
    return
  }
  const target = point ?? editor.getViewportPageBounds().center
  editor.markHistoryStoppingPoint('insert gallery item')
  if (item.kind === 'image') {
    await insertImage(editor, item, target)
  } else if (item.content !== null) {
    // Same path as tldraw's paste-at-cursor: fresh shape ids, centred on the point, selected.
    editor.putContentOntoCurrentPage(item.content as unknown as TLContent, { point: target, select: true })
  }
  editor.focus()
}
