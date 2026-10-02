import { describe, expect, it } from 'vitest'

import { galleryItem } from '../test/gallery'
import { matchesGallerySearch, normalizeTag, parseTags, tagsProblem } from './galleryLabels'

describe('parseTags', () => {
  it('should split on commas, lower-case, collapse spaces and drop repeats', () => {
    expect(parseTags(' AWS,  Message   Queue ,aws,, ')).toEqual(['aws', 'message queue'])
    expect(parseTags('')).toEqual([])
    expect(normalizeTag('  K8S\t Cluster ')).toBe('k8s cluster')
  })
})

describe('tagsProblem', () => {
  it('should accept technology names in any language', () => {
    expect(tagsProblem(['c++', 'c#', 'ci/cd', 'node.js', 'event-driven', 'snake_case', 'café', 'ação'])).toBeNull()
  })

  it('should refuse too many, too long or unsupported tags', () => {
    expect(tagsProblem(Array.from({ length: 11 }, (_, index) => `t${index}`))).toBe('Use at most 10 tags.')
    expect(tagsProblem(['a'.repeat(32)])).toBeNull()
    expect(tagsProblem(['a'.repeat(33)])).toBe('Tags can have at most 32 characters.')
    expect(tagsProblem(['<script>'])).toContain('“<script>” has unsupported characters')
  })
})

describe('matchesGallerySearch', () => {
  const logo = galleryItem({ name: 'Temporal Logo', tags: ['workflow', 'brand'], description: 'Dark background' })

  it('should match every word against the name, the description and the tags', () => {
    expect(matchesGallerySearch(logo, '', null)).toBe(true)
    expect(matchesGallerySearch(logo, 'temporal', null)).toBe(true)
    expect(matchesGallerySearch(logo, 'WORKFLOW dark', null)).toBe(true)
    expect(matchesGallerySearch(logo, 'temporal kafka', null)).toBe(false)
    expect(matchesGallerySearch(galleryItem(), 'balancer', null)).toBe(true)
  })

  it('should filter by an exact tag', () => {
    expect(matchesGallerySearch(logo, '', 'brand')).toBe(true)
    expect(matchesGallerySearch(logo, '', 'bran')).toBe(false)
    expect(matchesGallerySearch(logo, 'logo', 'workflow')).toBe(true)
  })
})
