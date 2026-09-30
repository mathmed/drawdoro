import { describe, expect, it } from 'vitest'

import { claudeCodeCommand, claudeDesktopConfig, mcpConfig } from './mcp'

const URL = 'https://mcp.example.com/mcp'

describe('mcp connection snippets', () => {
  it('should default to the local MCP server', () => {
    expect(mcpConfig.url).toBe('http://localhost:8001/mcp')
  })

  it('should put the personal key in the Claude Code command', () => {
    const command = claudeCodeCommand('ddk_secret', URL)

    expect(command).toContain(`--transport http ${mcpConfig.serverName} ${URL}`)
    expect(command).toContain('--header "X-API-Key: ddk_secret"')
  })

  it('should use a placeholder until a key is generated', () => {
    expect(claudeCodeCommand(null, URL)).toContain('X-API-Key: <your-personal-key>')
  })

  it('should build a Claude Desktop config that reaches the server through mcp-remote', () => {
    const config = JSON.parse(claudeDesktopConfig('ddk_secret', URL))
    const server = config.mcpServers[mcpConfig.serverName]

    expect(server.command).toBe('npx')
    expect(server.args).toEqual(['-y', 'mcp-remote', URL, '--header', 'X-API-Key:${API_KEY}'])
    expect(server.env).toEqual({ API_KEY: 'ddk_secret' })
  })
})
