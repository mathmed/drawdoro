import { Check, Copy, Link2, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { shareDiagram } from '../../api/diagrams'
import { toast } from '../../store/useToastStore'
import Modal from '../ui/Modal'

export default function ShareDialog({ diagramId, onClose }: { diagramId: string; onClose: () => void }) {
  const [link, setLink] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let active = true
    void shareDiagram(diagramId)
      .then((token) => {
        if (active) {
          setLink(`${window.location.origin}/share/${token}`)
        }
      })
      .catch(() => {
        if (active) {
          onClose()
        }
      })
    return () => {
      active = false
    }
  }, [diagramId, onClose])

  async function handleCopy(): Promise<void> {
    if (link === null) {
      return
    }
    try {
      await navigator.clipboard.writeText(link)
      setCopied(true)
      toast('Link copied to clipboard', 'success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast('Could not copy the link', 'error')
    }
  }

  return (
    <Modal
      title="Share diagram"
      description="Anyone with this link can open the diagram. Guests can join by entering just their name."
      onClose={onClose}
      footer={
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Done
        </button>
      }
    >
      <div className="field">
        <label className="field-label" htmlFor="share-link">
          Shareable link
        </label>
        {link === null ? (
          <div className="full-center" style={{ height: 'auto', padding: '12px 0' }}>
            <Loader2 size={16} className="spinner" /> Generating link…
          </div>
        ) : (
          <div className="share-link-row">
            <span className="share-link-icon">
              <Link2 size={15} />
            </span>
            <input id="share-link" className="input" readOnly value={link} onFocus={(event) => event.target.select()} />
            <button type="button" className="btn btn-primary btn-icon" aria-label="Copy link" onClick={() => void handleCopy()}>
              {copied ? <Check size={15} /> : <Copy size={15} />}
            </button>
          </div>
        )}
      </div>
    </Modal>
  )
}
