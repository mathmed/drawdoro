import { BookmarkPlus, CircleAlert, ImagePlus, Images, Pencil, RotateCw, Search, Shapes, Trash2, X } from 'lucide-react'
import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from 'react'

import type { GalleryItemSummary } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog } from '../../store/useDialogStore'
import { useGalleryStore } from '../../store/useGalleryStore'
import {
  addImageToGallery,
  canSaveSelection,
  GALLERY_DRAG_TYPE,
  GALLERY_IMAGE_TYPES,
  insertGalleryItem,
  saveSelectionToGallery,
} from '../../utils/gallery'
import { matchesGallerySearch } from '../../utils/galleryLabels'
import EmptyState from '../ui/EmptyState'
import LoadingGate from '../ui/loading/LoadingGate'
import { Skeleton, SkeletonGroup } from '../ui/loading/Skeleton'
import Spinner from '../ui/loading/Spinner'
import GalleryItemDialog from './GalleryItemDialog'

function hasFiles(event: DragEvent): boolean {
  return event.dataTransfer.types.includes('Files')
}

// Tiles show a few tags; the rest are still searchable.
const TILE_TAGS = 3
const SKELETON_TILE_NAMES = ['70%', '52%', '62%', '44%', '58%', '66%']

function TileSkeleton({ nameWidth }: { nameWidth: string }) {
  return (
    <div className="gallery-tile gallery-tile-skeleton">
      <div className="gallery-tile-preview">
        <Skeleton width="100%" height="100%" />
      </div>
      <div className="gallery-tile-footer">
        <Skeleton className="skeleton-line" width={nameWidth} />
      </div>
    </div>
  )
}

function GallerySkeleton() {
  return (
    <SkeletonGroup label="Loading gallery">
      <div className="gallery-grid">
        {SKELETON_TILE_NAMES.map((width) => (
          <TileSkeleton key={width} nameWidth={width} />
        ))}
      </div>
    </SkeletonGroup>
  )
}

interface GalleryTileProps {
  item: GalleryItemSummary
  busy: boolean
  onInsert: () => void
  onTagClick: (tag: string) => void
}

function GalleryTile({ item, busy, onInsert, onTagClick }: GalleryTileProps) {
  const remove = useGalleryStore((state) => state.remove)
  const [editing, setEditing] = useState(false)

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
        aria-busy={busy}
        className="gallery-tile-preview"
        title={`Insert “${item.name}” — or drag it onto the canvas${item.description !== null ? `\n\n${item.description}` : ''}`}
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
            <Spinner size={18} />
          </span>
        ) : null}
      </button>
      <div className="gallery-tile-footer">
        <span className="gallery-tile-name" title={item.name}>
          {item.name}
        </span>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-sm"
          aria-label={`Edit ${item.name}`}
          title="Rename, tag or describe"
          onClick={() => setEditing(true)}
        >
          <Pencil size={12} />
        </button>
        <button type="button" className="btn btn-ghost btn-icon btn-sm" aria-label={`Delete ${item.name}`} onClick={() => void handleDelete()}>
          <Trash2 size={12} />
        </button>
      </div>
      {item.tags.length > 0 ? (
        <div className="gallery-tags gallery-tile-tags">
          {item.tags.slice(0, TILE_TAGS).map((tag) => (
            <button
              key={tag}
              type="button"
              className="gallery-tag"
              title={`Show items tagged “${tag}”`}
              onClick={() => onTagClick(tag)}
            >
              {tag}
            </button>
          ))}
          {item.tags.length > TILE_TAGS ? (
            <span className="gallery-tag-more" title={item.tags.slice(TILE_TAGS).join(', ')}>
              +{item.tags.length - TILE_TAGS}
            </span>
          ) : null}
        </div>
      ) : null}
      {editing ? <GalleryItemDialog item={item} onClose={() => setEditing(false)} /> : null}
    </div>
  )
}

export default function GalleryPanel() {
  const editor = useAppStore((state) => state.editor)
  const items = useGalleryStore((state) => state.items)
  const status = useGalleryStore((state) => state.status)
  const load = useGalleryStore((state) => state.load)

  const [query, setQuery] = useState('')
  const [activeTag, setActiveTag] = useState<string | null>(null)
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

  const visible = items.filter((item) => matchesGallerySearch(item, query, activeTag))

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

  // 'idle' too: the first render happens before the load starts, and must not flash the empty state.
  const isFirstLoad = (status === 'idle' || status === 'loading') && items.length === 0

  function renderBody() {
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
    if (items.length === 0 && uploading === 0) {
      return (
        <EmptyState
          icon={<Images size={20} />}
          title="Your gallery is empty"
          description="Right-click a selection and choose “Save to gallery”, or drop an image here. Saved items can be reused in any diagram."
        />
      )
    }
    if (visible.length === 0 && uploading === 0) {
      const searched = [query.trim(), activeTag !== null ? `tag “${activeTag}”` : ''].filter((part) => part !== '')
      return <EmptyState icon={<Search size={20} />} title={`No items match ${searched.join(' with ')}`} />
    }
    return (
      <div className="gallery-grid reveal">
        {uploading > 0 ? (
          <span className="sr-only" role="status">
            {uploading === 1 ? 'Adding 1 image to the gallery' : `Adding ${uploading} images to the gallery`}
          </span>
        ) : null}
        {Array.from({ length: uploading }, (_, index) => (
          <TileSkeleton key={`upload-${index}`} nameWidth={SKELETON_TILE_NAMES[index % SKELETON_TILE_NAMES.length]} />
        ))}
        {visible.map((item) => (
          <GalleryTile
            key={item.id}
            item={item}
            busy={insertingId === item.id}
            onInsert={() => void insert(item.id)}
            onTagClick={setActiveTag}
          />
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
          <input
            className="input"
            placeholder="Search names and tags…"
            aria-label="Search gallery"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
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
          aria-busy={uploading > 0}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading > 0 ? <Spinner size={15} /> : <ImagePlus size={15} />}
        </button>
        <input ref={fileInputRef} type="file" accept={GALLERY_IMAGE_TYPES.join(',')} multiple hidden onChange={handleFileInput} />
      </div>
      {activeTag !== null ? (
        <div className="gallery-filter">
          <span>Tagged</span>
          <button type="button" className="gallery-tag" aria-label={`Stop filtering by ${activeTag}`} onClick={() => setActiveTag(null)}>
            {activeTag} <X size={11} />
          </button>
        </div>
      ) : null}
      <div className="scroll" style={{ flex: 1 }} aria-busy={isFirstLoad}>
        <LoadingGate loading={isFirstLoad} fallback={<GallerySkeleton />}>
          {renderBody}
        </LoadingGate>
      </div>
      <div className="gallery-hint">Click to insert at the centre of the view, or drag onto the canvas.</div>
    </div>
  )
}
