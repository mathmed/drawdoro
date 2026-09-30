import { branding } from './branding'

// Where people point Claude at: the MCP server's streamable HTTP endpoint.
const DEFAULT_MCP_URL = 'http://localhost:8001/mcp'
const KEY_PLACEHOLDER = '<your-personal-key>'

export const mcpConfig = {
  url: import.meta.env.VITE_MCP_URL?.trim() || DEFAULT_MCP_URL,
  serverName: branding.slug,
} as const

export function claudeCodeCommand(apiKey: string | null, url: string = mcpConfig.url): string {
  const key = apiKey ?? KEY_PLACEHOLDER
  return `claude mcp add --transport http ${mcpConfig.serverName} ${url} --header "X-API-Key: ${key}"`
}

// Claude Desktop reaches remote servers through the mcp-remote bridge.
export function claudeDesktopConfig(apiKey: string | null, url: string = mcpConfig.url): string {
  const config = {
    mcpServers: {
      [mcpConfig.serverName]: {
        command: 'npx',
        args: ['-y', 'mcp-remote', url, '--header', 'X-API-Key:${API_KEY}'],
        env: { API_KEY: apiKey ?? KEY_PLACEHOLDER },
      },
    },
  }
  return JSON.stringify(config, null, 2)
}
