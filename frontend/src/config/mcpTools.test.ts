import { describe, expect, it } from 'vitest'

import { groupTools, mcpToolManifest, REQUIREMENT_LABELS, toolMatches, type McpToolManifest } from './mcpTools'

const SAMPLE: McpToolManifest = {
  areas: [
    { id: 'comments', title: 'Comments' },
    { id: 'gallery', title: 'Personal gallery' },
    { id: 'empty', title: 'Nothing here' },
  ],
  tools: [
    {
      name: 'add_comment',
      area: 'comments',
      requires: ['editor_role'],
      read_only: false,
      destructive: false,
      summary: 'Write a comment.',
      description: ['Write a comment.', 'Plain text only.'],
      parameters: [{ name: 'element_id', required: false, description: 'Shape to anchor it to.' }],
    },
    {
      name: 'list_gallery_items',
      area: 'gallery',
      requires: ['personal_key'],
      read_only: true,
      destructive: false,
      summary: 'List the gallery.',
      description: ['List the gallery.'],
      parameters: [],
    },
  ],
}

describe('mcpToolManifest', () => {
  it('should list the tools the MCP server registers, in known areas', () => {
    const names = mcpToolManifest.tools.map((tool) => tool.name)
    const areas = new Set(mcpToolManifest.areas.map((area) => area.id))

    expect(names).toEqual(expect.arrayContaining(['list_workspaces', 'edit_shapes', 'add_comment', 'resolve_comment']))
    expect(names).toEqual(
      expect.arrayContaining(['list_gallery_items', 'get_gallery_item', 'insert_gallery_item', 'update_gallery_item']),
    )
    expect(new Set(names).size).toBe(names.length)
    expect(mcpToolManifest.tools.every((tool) => areas.has(tool.area) && tool.summary !== '')).toBe(true)
    expect(
      mcpToolManifest.tools.every((tool) => tool.requires.every((requirement) => requirement in REQUIREMENT_LABELS)),
    ).toBe(true)
  })

  it('should mark the gallery tools as needing a personal key', () => {
    const gallery = mcpToolManifest.tools.filter((tool) => tool.area === 'gallery')
    expect(gallery.length).toBeGreaterThanOrEqual(4)
    expect(gallery.every((tool) => tool.requires.includes('personal_key'))).toBe(true)
  })
})

describe('toolMatches', () => {
  const [comment] = SAMPLE.tools

  it('should search names, descriptions and parameters with every word', () => {
    expect(toolMatches(comment, '')).toBe(true)
    expect(toolMatches(comment, 'add_comment')).toBe(true)
    expect(toolMatches(comment, 'ADD comment')).toBe(true)
    expect(toolMatches(comment, 'plain')).toBe(true)
    expect(toolMatches(comment, 'anchor element_id')).toBe(true)
    expect(toolMatches(comment, 'comment gallery')).toBe(false)
  })
})

describe('groupTools', () => {
  it('should group tools by area in order and drop empty areas', () => {
    const groups = groupTools(SAMPLE, '', null)
    expect(groups.map((group) => [group.area.id, group.tools.map((tool) => tool.name)])).toEqual([
      ['comments', ['add_comment']],
      ['gallery', ['list_gallery_items']],
    ])
  })

  it('should filter by area and search', () => {
    expect(groupTools(SAMPLE, '', 'gallery').map((group) => group.area.id)).toEqual(['gallery'])
    expect(groupTools(SAMPLE, 'gallery', 'comments')).toEqual([])
    expect(groupTools(SAMPLE, 'plain', null).map((group) => group.area.id)).toEqual(['comments'])
  })
})
