import { BookmarkPlus, CircleAlert, ImagePlus, Images, Loader2, Pencil, RotateCw, Search, Shapes, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from 'react'

import type { GalleryItemSummary } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog, promptDialog } from '../../store/useDialogStore'
import { useGalleryStore } from '../../store/useGalleryStore'
import {
  addImageToGallery,
  canSaveSelection,
  GALLERY_DRAG_TYPE,
  GALLERY_IMAGE_TYPES,
  insertGalleryItem,
  saveSelectionToGallery,
} from '../../utils/gallery'
import EmptyState from '../ui/EmptyState'

function hasFiles(event: DragEvent): boolean {
  return event.dataTransfer.types.includes('Files')
}

function GalleryTile({ item, busy, onInsert }: { item: GalleryItemSummary; busy: boolean; onInsert: () => void }) {
  const rename = useGalleryStore((state) => state.rename)
  const remove = useGalleryStore((state) => state.remove)

  async function handleRename(): Promise<void> {
    const name = await promptDialog({ title: 'Rename item', label: 'Name', initialValue: item.name, confirmLabel: 'Rename' })
    if (name !== null && name !== item.name) {
      await rename(item.id, name)
    }
  }

  async function handleDelete(): Promise<void> {
    const confirmed = await confirmDialog({
      title: `Delete “${item.name}”?`,
      description: 'It is removed from your gallery. Diagrams that already use it keep their copy.',
      confirmLabel: 'Delete',
      danger: true,
    })
    if (confirmed) {
      await remove(item.id)
    }
  }

  return (
    <div className="gallery-tile" data-busy={busy}>
      <button
        type="button"
        className="gallery-tile-preview"
        title={`Insert “${item.name}” — or drag it onto the canvas`}
        draggable
        onDragStart={(event) => {
          event.dataTransfer.setData(GALLERY_DRAG_TYPE, item.id)
          event.dataTransfer.effectAllowed = 'copy'
        }}
        onClick={onInsert}
      >
        {item.thumbnail_base64 !== null ? (
          <img src={`data:image/png;base64,${item.thumbnail_base64}`} alt="" draggable={false} />
        ) : (
          <span className="gallery-tile-placeholder">{item.kind === 'image' ? <Images size={22} /> : <Shapes size={22} />}</span>
        )}
        {busy ? (
          <span className="gallery-tile-spinner">
            <Loader2 size={16} className="spinner" />
          </span>
        ) : null}
      </button>
      <div className="gallery-tile-footer">
        <span className="gallery-tile-name" title={item.name}>
          {item.name}
        </span>
        <button type="button" className="btn btn-ghost btn-icon btn-sm" aria-label={`Rename ${item.name}`} onClick={() => void handleRename()}>
          <Pencil size={12} />
        </button>
        <button type="button" className="btn btn-ghost btn-icon btn-sm" aria-label={`Delete ${item.name}`} onClick={() => void handleDelete()}>
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  )
}

export default function GalleryPanel() {
  const editor = useAppStore((state) => state.editor)
  const items = useGalleryStore((state) => state.items)
  const status = useGalleryStore((state) => state.status)
  const load = useGalleryStore((state) => state.load)

  const [query, setQuery] = useState('')
  const [insertingId, setInsertingId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(0)
  const [isDropTarget, setIsDropTarget] = useState(false)
  const [hasSelection, setHasSelection] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Refresh on every open; the cached items stay visible meanwhile.
  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (editor === null) {
      return
    }
    const update = (): void => setHasSelection(canSaveSelection(editor))
    update()
    return editor.store.listen(update, { scope: 'session' })
  }, [editor])

  const normalizedQuery = query.trim().toLowerCase()
  const visible = items.filter((item) => item.name.toLowerCase().includes(normalizedQuery))

  async function insert(itemId: string): Promise<void> {
    if (editor === null) {
      return
    }
    setInsertingId(itemId)
    try {
      await insertGalleryItem(editor, itemId)
    } finally {
      setInsertingId(null)
    }
  }

  async function upload(files: File[]): Promise<void> {
    setUploading((count) => count + files.length)
    for (const file of files) {
      try {
        await addImageToGallery(file)
      } finally {
        setUploading((count) => count - 1)
      }
    }
  }

  function handleFileInput(event: ChangeEvent<HTMLInputElement>): void {
    void upload(Array.from(event.target.files ?? []))
    event.target.value = ''
  }

  function handleDrop(event: DragEvent): void {
    if (!hasFiles(event)) {
      return
    }
    event.preventDefault()
    setIsDropTarget(false)
    void upload(Array.from(event.dataTransfer.files))
  }

  function renderBody() {
    if (status === 'loading' && items.length === 0) {
      return (
        <div className="full-center gallery-status">
          <Loader2 size={16} className="spinner" /> Loading gallery…
        </div>
      )
    }
    if (status === 'error' && items.length === 0) {
      return (
        <EmptyState
          icon={<CircleAlert size={20} />}
          title="Could not load your gallery"
          action={
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>
              <RotateCw size={13} /> Try again
            </button>
          }
        />
      )
    }
    if (items.length === 0) {
      return (
        <EmptyState
          icon={<Images size={20} />}
          title="Your gallery is empty"
          description="Right-click a selection and choose “Save to gallery”, or drop an image here. Saved items can be reused in any diagram."
        />
      )
    }
    if (visible.length === 0) {
      return <EmptyState icon={<Search size={20} />} title={`No items match “${query.trim()}”`} />
    }
    return (
      <div className="gallery-grid">
        {visible.map((item) => (
          <GalleryTile key={item.id} item={item} busy={insertingId === item.id} onInsert={() => void insert(item.id)} />
        ))}
      </div>
    )
  }

  return (
    <div
      className="gallery-panel"
      data-drop-target={isDropTarget}
      onDragOver={(event) => {
        if (hasFiles(event)) {
          event.preventDefault()
          setIsDropTarget(true)
        }
      }}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setIsDropTarget(false)
        }
      }}
      onDrop={handleDrop}
    >
      <div className="panel-toolbar">
        <div className="gallery-search">
          <Search size={13} />
          <input className="input" placeholder="Search gallery…" value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          aria-label="Save selection to gallery"
          title="Save selection to gallery"
          disabled={!hasSelection || editor === null}
          onClick={() => editor !== null && void saveSelectionToGallery(editor)}
        >
          <BookmarkPlus size={15} />
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          aria-label="Upload image"
          title="Upload image"
          disabled={uploading > 0}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading > 0 ? <Loader2 size={15} className="spinner" /> : <ImagePlus size={15} />}
        </button>
        <input ref={fileInputRef} type="file" accept={GALLERY_IMAGE_TYPES.join(',')} multiple hidden onChange={handleFileInput} />
      </div>
      <div className="scroll" style={{ flex: 1 }}>
        {renderBody()}
      </div>
      <div className="gallery-hint">Click to insert at the centre of the view, or drag onto the canvas.</div>
    </div>
  )
}
