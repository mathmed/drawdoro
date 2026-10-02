import { useState, type FormEvent } from 'react'

import type { GalleryItemChanges, GalleryItemSummary } from '../../api/types'
import { useGalleryStore } from '../../store/useGalleryStore'
import {
  GALLERY_MAX_DESCRIPTION_LENGTH,
  GALLERY_MAX_NAME_LENGTH,
  parseTags,
  tagsProblem,
} from '../../utils/galleryLabels'
import Spinner from '../ui/loading/Spinner'
import Modal from '../ui/Modal'

function changesOf(item: GalleryItemSummary, name: string, tags: string[], description: string): GalleryItemChanges {
  const changes: GalleryItemChanges = {}
  if (name.trim() !== item.name) {
    changes.name = name.trim()
  }
  if (tags.join(',') !== item.tags.join(',')) {
    changes.tags = tags
  }
  if (description.trim() !== (item.description ?? '')) {
    changes.description = description.trim()
  }
  return changes
}

// Name, tags and description of a gallery item: what search (and agents) use to find it.
export default function GalleryItemDialog({ item, onClose }: { item: GalleryItemSummary; onClose: () => void }) {
  const update = useGalleryStore((state) => state.update)
  const [name, setName] = useState(item.name)
  const [tagsInput, setTagsInput] = useState(item.tags.join(', '))
  const [description, setDescription] = useState(item.description ?? '')
  const [saving, setSaving] = useState(false)

  const tags = parseTags(tagsInput)
  const problem = name.trim() === '' ? 'The name is required.' : tagsProblem(tags)
  const changes = changesOf(item, name, tags, description)
  const unchanged = Object.keys(changes).length === 0

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault()
    if (problem !== null || unchanged) {
      return
    }
    setSaving(true)
    const saved = await update(item.id, changes)
    setSaving(false)
    if (saved) {
      onClose()
    }
  }

  return (
    <Modal
      title="Edit gallery item"
      description="Tags and the description make the item easy to find, in search and for your Claude."
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            form="gallery-item-form"
            className="btn btn-primary"
            disabled={problem !== null || unchanged || saving}
            aria-busy={saving}
          >
            {saving ? <Spinner size={14} /> : null}
            Save
          </button>
        </>
      }
    >
      <form id="gallery-item-form" className="gallery-item-form" onSubmit={(event) => void handleSubmit(event)}>
        <div className="field">
          <label className="field-label" htmlFor="gallery-item-name">
            Name
          </label>
          <input
            id="gallery-item-name"
            className="input"
            autoFocus
            maxLength={GALLERY_MAX_NAME_LENGTH}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="gallery-item-tags">
            Tags
          </label>
          <input
            id="gallery-item-tags"
            className="input"
            placeholder="e.g. aws, message queue"
            value={tagsInput}
            onChange={(event) => setTagsInput(event.target.value)}
          />
          <p className="field-hint">Separate tags with commas. They are saved in lower case.</p>
          {tags.length > 0 ? (
            <div className="gallery-tags" aria-label="Tags preview">
              {tags.map((tag) => (
                <span key={tag} className="gallery-tag">
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <div className="field">
          <label className="field-label" htmlFor="gallery-item-description">
            Description
          </label>
          <textarea
            id="gallery-item-description"
            className="textarea"
            rows={3}
            maxLength={GALLERY_MAX_DESCRIPTION_LENGTH}
            placeholder="What it shows and when to use it"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <p className="field-hint">
            {description.trim().length}/{GALLERY_MAX_DESCRIPTION_LENGTH}
          </p>
        </div>
        {problem !== null ? (
          <p className="field-error" role="alert">
            {problem}
          </p>
        ) : null}
      </form>
    </Modal>
  )
}
