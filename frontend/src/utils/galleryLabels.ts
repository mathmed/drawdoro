import type { GalleryItemSummary } from '../api/types'

// Same limits and rules as the API, so problems show up while typing; the API stays the judge.
export const GALLERY_MAX_TAGS = 10
export const GALLERY_MAX_TAG_LENGTH = 32
export const GALLERY_MAX_DESCRIPTION_LENGTH = 500
export const GALLERY_MAX_NAME_LENGTH = 255
// Letters and digits of any language plus a few separators found in technology names.
const TAG_PATTERN = /^[\p{L}\p{M}\p{N}_ .+#/-]+$/u

export function normalizeTag(raw: string): string {
  return raw.replace(/\s+/g, ' ').trim().toLowerCase()
}

// Tags are typed as a comma-separated list; repeats and empty entries are dropped.
export function parseTags(input: string): string[] {
  const tags: string[] = []
  for (const part of input.split(',')) {
    const tag = normalizeTag(part)
    if (tag !== '' && !tags.includes(tag)) {
      tags.push(tag)
    }
  }
  return tags
}

export function tagsProblem(tags: string[]): string | null {
  if (tags.length > GALLERY_MAX_TAGS) {
    return `Use at most ${GALLERY_MAX_TAGS} tags.`
  }
  const long = tags.find((tag) => tag.length > GALLERY_MAX_TAG_LENGTH)
  if (long !== undefined) {
    return `Tags can have at most ${GALLERY_MAX_TAG_LENGTH} characters.`
  }
  const invalid = tags.find((tag) => !TAG_PATTERN.test(tag))
  if (invalid !== undefined) {
    return `“${invalid}” has unsupported characters: use letters, digits, spaces and . + # / - _`
  }
  return null
}

// Every word of the query must appear in the name, the description or a tag; the tag filter must
// match one tag exactly.
export function matchesGallerySearch(item: GalleryItemSummary, query: string, tag: string | null): boolean {
  if (tag !== null && !item.tags.includes(tag)) {
    return false
  }
  const haystack = [item.name, item.description ?? '', ...item.tags].join(' ').toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter((word) => word !== '')
    .every((word) => haystack.includes(word))
}
