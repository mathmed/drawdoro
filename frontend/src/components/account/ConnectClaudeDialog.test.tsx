import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createApiKey, listApiKeys } from '../../api/apiKeys'
import ConnectClaudeDialog from './ConnectClaudeDialog'

const authConfig = vi.hoisted(() => ({ enabled: true }))

vi.mock('../../auth/config', () => ({ authConfig }))
vi.mock('../../api/apiKeys')

beforeEach(() => {
  vi.mocked(listApiKeys).mockResolvedValue([])
})

describe('ConnectClaudeDialog', () => {
  it('should show the MCP server URL and a Claude Code command with a key placeholder', async () => {
    render(<ConnectClaudeDialog onClose={vi.fn()} />)

    expect(screen.getByRole('textbox', { name: 'MCP server URL' })).toHaveValue('http://localhost:8001/mcp')
    expect(screen.getByLabelText('Claude Code command')).toHaveTextContent('X-API-Key: <your-personal-key>')
    expect(await screen.findByText('No personal keys yet')).toBeInTheDocument()
  })

  it('should fill the generated key into the connection commands', async () => {
    vi.mocked(createApiKey).mockResolvedValue({
      id: 'k1',
      label: 'Claude',
      prefix: 'ddk_ab12',
      created_at: '2026-01-01T10:00:00Z',
      last_used_at: null,
      secret: 'ddk_full_secret',
    })
    render(<ConnectClaudeDialog onClose={vi.fn()} />)
    await screen.findByText('No personal keys yet')

    await userEvent.click(screen.getByRole('button', { name: /Generate key/ }))

    expect(await screen.findByLabelText('Claude Code command')).toHaveTextContent('X-API-Key: ddk_full_secret')
    await userEvent.click(screen.getByRole('tab', { name: 'Claude Desktop' }))
    expect(screen.getByLabelText('Claude Desktop configuration')).toHaveTextContent('"API_KEY": "ddk_full_secret"')
  })
})
