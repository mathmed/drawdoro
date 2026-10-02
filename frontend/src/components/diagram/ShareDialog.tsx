import { Check, Copy, Link2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { shareDiagram } from '../../api/diagrams'
import { toast } from '../../store/useToastStore'
import LoadingGate from '../ui/loading/LoadingGate'
import { Skeleton, SkeletonGroup } from '../ui/loading/Skeleton'
import Modal from '../ui/Modal'

// Same boxes as the link row (icon, field, copy button), so the dialog keeps its size.
function LinkSkeleton() {
  return (
    <SkeletonGroup label="Generating link">
      <div className="share-link-row">
        <Skeleton width={32} height={32} radius="var(--radius-md)" />
        <Skeleton height={32} radius="var(--radius-md)" className="share-link-skeleton-field" />
        <Skeleton width={32} height={32} radius="var(--radius-md)" />
      </div>
    </SkeletonGroup>
  )
}

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
        <LoadingGate
          loading={link === null}
          placeholder={<div className="share-link-row share-link-placeholder" />}
          fallback={<LinkSkeleton />}
        >
          {() => (
            <div className="share-link-row reveal">
              <span className="share-link-icon">
                <Link2 size={15} />
              </span>
              <input id="share-link" className="input" readOnly value={link ?? ''} onFocus={(event) => event.target.select()} />
              <button type="button" className="btn btn-primary btn-icon" aria-label="Copy link" onClick={() => void handleCopy()}>
                {copied ? <Check size={15} /> : <Copy size={15} />}
              </button>
            </div>
          )}
        </LoadingGate>
      </div>
    </Modal>
  )
}
