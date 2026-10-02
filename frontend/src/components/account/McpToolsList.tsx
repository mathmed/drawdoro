import { Check, ChevronRight, Copy, KeyRound, PencilLine, Search } from 'lucide-react'
import { useState } from 'react'

import {
  groupTools,
  mcpToolManifest,
  REQUIREMENT_LABELS,
  type McpTool,
  type McpToolManifest,
  type McpToolRequirement,
} from '../../config/mcpTools'
import { toast } from '../../store/useToastStore'
import EmptyState from '../ui/EmptyState'

const COPIED_FEEDBACK_MS = 2000
const REQUIREMENT_ICONS: Record<McpToolRequirement, typeof KeyRound> = {
  personal_key: KeyRound,
  editor_role: PencilLine,
}

function CopyNameButton({ name }: { name: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(name)
      setCopied(true)
      setTimeout(() => setCopied(false), COPIED_FEEDBACK_MS)
    } catch {
      toast('Could not copy to the clipboard', 'error')
    }
  }

  return (
    <button
      type="button"
      className="btn btn-ghost btn-icon btn-sm"
      aria-label={`Copy ${name}`}
      data-tooltip={copied ? 'Copied' : 'Copy name'}
      onClick={() => void handleCopy()}
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
    </button>
  )
}

function ToolRow({ tool }: { tool: McpTool }) {
  return (
    <li className="mcp-tool">
      <div className="mcp-tool-header">
        <code className="mcp-tool-name">{tool.name}</code>
        <CopyNameButton name={tool.name} />
        <span className="mcp-tool-badges">
          {tool.requires.map((requirement) => {
            const Icon = REQUIREMENT_ICONS[requirement]
            return (
              <span key={requirement} className="badge badge-neutral" title={REQUIREMENT_LABELS[requirement].hint}>
                <Icon size={11} /> {REQUIREMENT_LABELS[requirement].label}
              </span>
            )
          })}
        </span>
      </div>
      <p className="mcp-tool-summary">{tool.summary}</p>
      {tool.description.length > 1 || tool.parameters.length > 0 ? (
        <details className="mcp-tool-details">
          <summary>
            <ChevronRight size={12} /> Details
          </summary>
          {tool.description.slice(1).map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
          {tool.parameters.length > 0 ? (
            <dl className="mcp-tool-parameters">
              {tool.parameters.map((parameter) => (
                <div key={parameter.name}>
                  <dt>
                    <code>{parameter.name}</code>
                    {parameter.required ? <span className="mcp-tool-required"> required</span> : null}
                  </dt>
                  <dd>{parameter.description}</dd>
                </div>
              ))}
            </dl>
          ) : null}
        </details>
      ) : null}
    </li>
  )
}

// Every tool the MCP server offers, grouped by area, as the model sees them.
export default function McpToolsList({ manifest = mcpToolManifest }: { manifest?: McpToolManifest }) {
  const [query, setQuery] = useState('')
  const [areaId, setAreaId] = useState<string | null>(null)
  const groups = groupTools(manifest, query, areaId)
  const shown = groups.reduce((total, group) => total + group.tools.length, 0)

  return (
    <div className="mcp-tools">
      <p className="connect-step-hint">
        Claude can use these {manifest.tools.length} tools once connected. The descriptions are the ones Claude reads.
      </p>
      <div className="mcp-tools-filters">
        <div className="gallery-search">
          <Search size={13} />
          <input
            className="input"
            aria-label="Search tools"
            placeholder="Search tools…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <select
          className="select"
          aria-label="Area"
          value={areaId ?? ''}
          onChange={(event) => setAreaId(event.target.value === '' ? null : event.target.value)}
        >
          <option value="">All areas</option>
          {manifest.areas.map((area) => (
            <option key={area.id} value={area.id}>
              {area.title}
            </option>
          ))}
        </select>
      </div>
      {groups.length === 0 ? (
        <EmptyState icon={<Search size={20} />} title="No tools match your search" />
      ) : (
        <>
          <p className="mcp-tools-count" aria-live="polite">
            {shown === manifest.tools.length ? `${shown} tools` : `${shown} of ${manifest.tools.length} tools`}
          </p>
          {groups.map((group) => (
            <section key={group.area.id} className="mcp-tool-group" aria-label={group.area.title}>
              <h3 className="connect-step-title">
                {group.area.title} <span className="count">{group.tools.length}</span>
              </h3>
              <ul className="mcp-tool-list">
                {group.tools.map((tool) => (
                  <ToolRow key={tool.name} tool={tool} />
                ))}
              </ul>
            </section>
          ))}
        </>
      )}
    </div>
  )
}
