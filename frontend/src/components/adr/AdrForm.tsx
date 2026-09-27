import { useState } from 'react'

import type { Adr, AdrStatus, CreateAdrData } from '../../api/types'
import { ADR_STATUSES } from './adrStatus'

interface AdrFormProps {
  initial?: Adr
  onSubmit: (data: CreateAdrData) => Promise<void>
  onCancel: () => void
}

const inputStyle: React.CSSProperties = {
  background: '#0f1117',
  color: '#e6edf3',
  border: '1px solid #30363d',
  borderRadius: 6,
  padding: '6px 8px',
  fontSize: 13,
  width: '100%',
  boxSizing: 'border-box',
}

const labelStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#8b949e',
  marginBottom: 4,
  display: 'block',
}

export default function AdrForm({ initial, onSubmit, onCancel }: AdrFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [context, setContext] = useState(initial?.context ?? '')
  const [decision, setDecision] = useState(initial?.decision ?? '')
  const [consequences, setConsequences] = useState(initial?.consequences ?? '')
  const [status, setStatus] = useState<AdrStatus>(initial?.status ?? 'proposed')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault()
    if (title.trim() === '') {
      return
    }
    setSaving(true)
    try {
      await onSubmit({
        title: title.trim(),
        context,
        decision,
        consequences,
        status,
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 12 }}
    >
      <div>
        <label style={labelStyle}>Title</label>
        <input style={inputStyle} value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>
      <div>
        <label style={labelStyle}>Context</label>
        <textarea
          style={{ ...inputStyle, resize: 'vertical', minHeight: 48 }}
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
      </div>
      <div>
        <label style={labelStyle}>Decision</label>
        <textarea
          style={{ ...inputStyle, resize: 'vertical', minHeight: 48 }}
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
        />
      </div>
      <div>
        <label style={labelStyle}>Consequences</label>
        <textarea
          style={{ ...inputStyle, resize: 'vertical', minHeight: 48 }}
          value={consequences}
          onChange={(e) => setConsequences(e.target.value)}
        />
      </div>
      <div>
        <label style={labelStyle}>Status</label>
        <select
          style={inputStyle}
          value={status}
          onChange={(e) => setStatus(e.target.value as AdrStatus)}
        >
          {ADR_STATUSES.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button
          type="button"
          onClick={onCancel}
          style={{
            background: '#21262d',
            color: '#e6edf3',
            border: '1px solid #30363d',
            borderRadius: 6,
            padding: '6px 12px',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          style={{
            background: '#2f81f7',
            color: '#e6edf3',
            border: '1px solid #30363d',
            borderRadius: 6,
            padding: '6px 12px',
            fontSize: 13,
            cursor: saving ? 'default' : 'pointer',
            opacity: saving ? 0.6 : 1,
          }}
        >
          Save
        </button>
      </div>
    </form>
  )
}
