import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

import { toast } from '../../store/useToastStore'

const COPIED_FEEDBACK_MS = 2000

interface CopyFieldProps {
  label: string
  value: string
  multiline?: boolean
}

// A read-only value with a copy button: links, commands, config snippets and secrets.
export default function CopyField({ label, value, multiline = false }: CopyFieldProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), COPIED_FEEDBACK_MS)
    } catch {
      toast('Could not copy to the clipboard', 'error')
    }
  }

  return (
    <div className="copy-field" data-multiline={multiline}>
      {multiline ? (
        <pre className="copy-field-value" aria-label={label}>
          {value}
        </pre>
      ) : (
        <input className="input copy-field-value" aria-label={label} readOnly value={value} onFocus={(event) => event.target.select()} />
      )}
      <button
        type="button"
        className="btn btn-secondary btn-icon btn-sm copy-field-button"
        aria-label={`Copy ${label.toLowerCase()}`}
        data-tooltip={copied ? 'Copied' : 'Copy'}
        onClick={() => void handleCopy()}
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </div>
  )
}
