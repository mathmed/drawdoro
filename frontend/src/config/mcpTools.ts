import manifest from './mcpTools.json'

// What the MCP server offers agents, generated from the tools it registers (`make mcp-manifest`);
// the MCP tests fail when mcpTools.json drifts from them. Descriptions are the ones the model reads.

export type McpToolRequirement = 'personal_key' | 'editor_role'

export interface McpToolParameter {
  name: string
  required: boolean
  description: string
}

export interface McpTool {
  name: string
  area: string
  requires: McpToolRequirement[]
  read_only: boolean
  destructive: boolean
  summary: string
  description: string[]
  parameters: McpToolParameter[]
}

export interface McpToolArea {
  id: string
  title: string
}

export interface McpToolGroup {
  area: McpToolArea
  tools: McpTool[]
}

export interface McpToolManifest {
  areas: McpToolArea[]
  tools: McpTool[]
}

export const mcpToolManifest = manifest as McpToolManifest

export const REQUIREMENT_LABELS: Record<McpToolRequirement, { label: string; hint: string }> = {
  personal_key: {
    label: 'Personal key',
    hint: 'Only works with your personal key: the shared service key has no personal gallery.',
  },
  editor_role: {
    label: 'Editor role',
    hint: 'Needs the editor or owner role in the workspace it changes.',
  },
}

function searchableText(tool: McpTool): string {
  const parameters = tool.parameters.map((parameter) => `${parameter.name} ${parameter.description}`)
  return [tool.name, tool.name.replace(/_/g, ' '), ...tool.description, ...parameters].join(' ').toLowerCase()
}

// Every word of the query must appear in the tool's name, description or parameters.
export function toolMatches(tool: McpTool, query: string): boolean {
  const text = searchableText(tool)
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter((word) => word !== '')
    .every((word) => text.includes(word))
}

// Areas in the server's order, each with its matching tools; areas left empty are dropped.
export function groupTools(source: McpToolManifest, query: string, areaId: string | null): McpToolGroup[] {
  return source.areas
    .filter((area) => areaId === null || area.id === areaId)
    .map((area) => ({
      area,
      tools: source.tools.filter((tool) => tool.area === area.id && toolMatches(tool, query)),
    }))
    .filter((group) => group.tools.length > 0)
}
