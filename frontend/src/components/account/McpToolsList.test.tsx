import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { mcpToolManifest, type McpToolManifest } from '../../config/mcpTools'
import McpToolsList from './McpToolsList'

const SAMPLE: McpToolManifest = {
  areas: [
    { id: 'comments', title: 'Comments' },
    { id: 'gallery', title: 'Personal gallery' },
  ],
  tools: [
    {
      name: 'add_comment',
      area: 'comments',
      requires: ['editor_role'],
      read_only: false,
      destructive: false,
      summary: 'Write a comment on a diagram.',
      description: ['Write a comment on a diagram.', 'Text is <b>plain</b>.'],
      parameters: [{ name: 'content', required: true, description: 'The comment text.' }],
    },
    {
      name: 'insert_gallery_item',
      area: 'gallery',
      requires: ['personal_key', 'editor_role'],
      read_only: false,
      destructive: false,
      summary: 'Insert a gallery item.',
      description: ['Insert a gallery item.'],
      parameters: [],
    },
  ],
}

describe('McpToolsList', () => {
  it('should group the tools by area with their requirements', () => {
    render(<McpToolsList manifest={SAMPLE} />)

    const comments = screen.getByRole('region', { name: 'Comments' })
    expect(within(comments).getByText('add_comment')).toBeInTheDocument()
    expect(within(comments).getByText('Write a comment on a diagram.')).toBeInTheDocument()
    expect(within(comments).getByText('Editor role')).toBeInTheDocument()
    expect(within(comments).queryByText('Personal key')).toBeNull()
    const gallery = screen.getByRole('region', { name: 'Personal gallery' })
    expect(within(gallery).getByText('Personal key')).toHaveAttribute(
      'title',
      expect.stringContaining('shared service key has no personal gallery'),
    )
    expect(screen.getByText('2 tools')).toBeInTheDocument()
  })

  it('should show details as plain text', () => {
    render(<McpToolsList manifest={SAMPLE} />)

    expect(screen.getByText('Text is <b>plain</b>.')).toBeInTheDocument()
    expect(document.querySelector('.mcp-tool b')).toBeNull()
    expect(screen.getByText('The comment text.')).toBeInTheDocument()
  })

  it('should search and filter by area', async () => {
    render(<McpToolsList manifest={SAMPLE} />)

    await userEvent.type(screen.getByRole('textbox', { name: 'Search tools' }), 'gallery')
    expect(screen.queryByRole('region', { name: 'Comments' })).toBeNull()
    expect(screen.getByText('1 of 2 tools')).toBeInTheDocument()

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Area' }), 'comments')
    expect(screen.getByText('No tools match your search')).toBeInTheDocument()

    await userEvent.clear(screen.getByRole('textbox', { name: 'Search tools' }))
    expect(screen.getByRole('region', { name: 'Comments' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Personal gallery' })).toBeNull()
  })

  it('should copy a tool name', async () => {
    const user = userEvent.setup()
    const writeText = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue()
    render(<McpToolsList manifest={SAMPLE} />)

    await user.click(screen.getByRole('button', { name: 'Copy insert_gallery_item' }))

    expect(writeText).toHaveBeenCalledWith('insert_gallery_item')
    expect(screen.getByRole('button', { name: 'Copy insert_gallery_item' })).toHaveAttribute('data-tooltip', 'Copied')
  })

  // The manifest is the server's own list (the MCP tests keep it in sync), so all of it must show.
  it('should list every real tool by default', () => {
    render(<McpToolsList />)

    expect(screen.getByText(`${mcpToolManifest.tools.length} tools`)).toBeInTheDocument()
    for (const tool of mcpToolManifest.tools) {
      expect(screen.getByText(tool.name, { selector: 'code' })).toBeInTheDocument()
    }
    for (const area of mcpToolManifest.areas) {
      expect(screen.getByRole('region', { name: area.title })).toBeInTheDocument()
    }
  })
})
