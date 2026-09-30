import { useState } from 'react'

import { branding } from '../../config/branding'
import { claudeCodeCommand, claudeDesktopConfig, mcpConfig } from '../../config/mcp'
import CopyField from '../ui/CopyField'
import Modal from '../ui/Modal'
import { ApiKeyManager } from './ApiKeysDialog'
import '../../styles/history.css'

type ClientTab = 'code' | 'desktop'

// Step-by-step guide to plug Claude into this app through the MCP server, with a personal key so
// the agent shows up as the user's own Claude.
export default function ConnectClaudeDialog({ onClose }: { onClose: () => void }) {
  const [secret, setSecret] = useState<string | null>(null)
  const [tab, setTab] = useState<ClientTab>('code')

  return (
    <Modal
      title="Connect Claude"
      description={`Let Claude read and edit your ${branding.name} diagrams. People with a diagram open see your Claude working, and every change it makes lands in the history.`}
      size="lg"
      onClose={onClose}
      footer={
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Done
        </button>
      }
    >
      <ol className="connect-steps">
        <li className="connect-step">
          <h3 className="connect-step-title">MCP server URL</h3>
          <CopyField label="MCP server URL" value={mcpConfig.url} />
        </li>
        <li className="connect-step">
          <h3 className="connect-step-title">Generate your personal key</h3>
          <p className="connect-step-hint">
            It identifies your Claude, so it shows up with your name. It's shown only once and filled into the
            commands below.
          </p>
          <ApiKeyManager onCreated={(created) => setSecret(created.secret)} />
        </li>
        <li className="connect-step">
          <h3 className="connect-step-title">Add it to Claude</h3>
          <div className="segmented connect-tabs" role="tablist" aria-label="Claude app">
            <button type="button" role="tab" aria-selected={tab === 'code'} aria-pressed={tab === 'code'} onClick={() => setTab('code')}>
              Claude Code
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'desktop'}
              aria-pressed={tab === 'desktop'}
              onClick={() => setTab('desktop')}
            >
              Claude Desktop
            </button>
          </div>
          {tab === 'code' ? (
            <>
              <p className="connect-step-hint">Run this in a terminal:</p>
              <CopyField label="Claude Code command" value={claudeCodeCommand(secret)} multiline />
            </>
          ) : (
            <>
              <p className="connect-step-hint">
                Add this to <code>claude_desktop_config.json</code> (Settings → Developer → Edit config) and restart
                Claude Desktop. It needs Node.js for <code>npx</code>.
              </p>
              <CopyField label="Claude Desktop configuration" value={claudeDesktopConfig(secret)} multiline />
            </>
          )}
        </li>
      </ol>
    </Modal>
  )
}
