import { KeyRound, Loader2, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { createApiKey, listApiKeys, revokeApiKey } from '../../api/apiKeys'
import type { ApiKey, CreatedApiKey } from '../../api/types'
import { authConfig } from '../../auth/config'
import { confirmDialog } from '../../store/useDialogStore'
import { timeAgo } from '../../utils/format'
import CopyField from '../ui/CopyField'
import EmptyState from '../ui/EmptyState'
import Modal from '../ui/Modal'
import '../../styles/history.css'

const LABEL_MAX_LENGTH = 60
const DEFAULT_LABEL = 'Claude'

interface ApiKeyManagerProps {
  // Called with every newly created key, e.g. to fill it into the connection commands.
  onCreated?: (created: CreatedApiKey) => void
}

// Personal keys let the user's Claude act as them: it shows up as "<name>'s Claude" in presence and
// in the history, and can do what the user can. The secret is shown once and stored only hashed.
export function ApiKeyManager({ onCreated }: ApiKeyManagerProps) {
  const [keys, setKeys] = useState<ApiKey[] | null>(null)
  const [label, setLabel] = useState(DEFAULT_LABEL)
  const [created, setCreated] = useState<CreatedApiKey | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    if (!authConfig.enabled) {
      return
    }
    let active = true
    void listApiKeys()
      .then((loaded) => {
        if (active) {
          setKeys(loaded)
        }
      })
      .catch(() => {
        if (active) {
          setKeys([])
        }
      })
    return () => {
      active = false
    }
  }, [])

  async function handleCreate(): Promise<void> {
    const trimmed = label.trim()
    if (trimmed === '') {
      return
    }
    setIsCreating(true)
    try {
      const key = await createApiKey(trimmed)
      setCreated(key)
      setKeys((current) => [key, ...(current ?? [])])
      setLabel(DEFAULT_LABEL)
      onCreated?.(key)
    } finally {
      setIsCreating(false)
    }
  }

  async function handleRevoke(key: ApiKey): Promise<void> {
    const confirmed = await confirmDialog({
      title: `Revoke "${key.label}"?`,
      description: 'Agents using this key stop working right away. This cannot be undone.',
      confirmLabel: 'Revoke',
      danger: true,
    })
    if (!confirmed) {
      return
    }
    await revokeApiKey(key.id)
    setKeys((current) => (current ?? []).filter((item) => item.id !== key.id))
    if (created?.id === key.id) {
      setCreated(null)
    }
  }

  if (!authConfig.enabled) {
    return (
      <p className="modal-note">
        Personal keys need sign-in. With login disabled, the MCP server acts with its own key (MCP_API_KEY).
      </p>
    )
  }

  return (
    <div className="api-keys">
      <form
        className="api-key-create"
        onSubmit={(event) => {
          event.preventDefault()
          void handleCreate()
        }}
      >
        <input
          className="input"
          aria-label="Key label"
          placeholder="Label, e.g. Claude on my laptop"
          maxLength={LABEL_MAX_LENGTH}
          value={label}
          onChange={(event) => setLabel(event.target.value)}
        />
        <button type="submit" className="btn btn-primary btn-sm" disabled={isCreating || label.trim() === ''}>
          {isCreating ? <Loader2 size={14} className="spinner" /> : <Plus size={14} />} Generate key
        </button>
      </form>

      {created !== null ? (
        <div className="api-key-secret" role="status">
          <strong>Copy your new key now: it won't be shown again.</strong>
          <CopyField label="New API key" value={created.secret} />
        </div>
      ) : null}

      {keys === null ? (
        <div className="full-center" style={{ height: 'auto', padding: 12 }}>
          <Loader2 size={16} className="spinner" />
        </div>
      ) : keys.length === 0 ? (
        <EmptyState icon={<KeyRound size={20} />} title="No personal keys yet" />
      ) : (
        <ul className="api-key-list">
          {keys.map((key) => (
            <li key={key.id} className="api-key">
              <KeyRound size={15} className="api-key-icon" />
              <span className="api-key-body">
                <span className="api-key-label">{key.label}</span>
                <span className="api-key-meta">
                  <code>{key.prefix}…</code> · created {timeAgo(key.created_at)} ·{' '}
                  {key.last_used_at === null ? 'never used' : `last used ${timeAgo(key.last_used_at)}`}
                </span>
              </span>
              <button
                type="button"
                className="btn btn-ghost btn-icon btn-sm"
                aria-label={`Revoke ${key.label}`}
                data-tooltip="Revoke"
                onClick={() => void handleRevoke(key)}
              >
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function ApiKeysDialog({ onClose }: { onClose: () => void }) {
  return (
    <Modal
      title="Personal API keys"
      description="Give a key to your Claude so it works on diagrams as you. Revoke it when you stop using it."
      onClose={onClose}
      footer={
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Done
        </button>
      }
    >
      <ApiKeyManager />
    </Modal>
  )
}
