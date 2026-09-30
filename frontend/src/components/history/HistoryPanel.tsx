import { Bot, History, Loader2, RotateCcw, Sparkles, User } from 'lucide-react'
import { useState } from 'react'
import { TldrawImage, type TLStoreSnapshot } from 'tldraw'

import { getRevision } from '../../api/revisions'
import type { DiagramRevision, DiagramRevisionDetail } from '../../api/types'
import { useRevisions } from '../../hooks/useRevisions'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog } from '../../store/useDialogStore'
import { toast } from '../../store/useToastStore'
import { colorFor } from '../../utils/avatar'
import { timeAgo } from '../../utils/format'
import { revisionAuthor, revisionDescription } from '../../utils/revisions'
import { shapeUtils } from '../canvas/shapeUtils'
import EmptyState from '../ui/EmptyState'
import UserAvatar from '../ui/UserAvatar'
import '../../styles/history.css'

function RevisionAvatar({ revision }: { revision: DiagramRevision }) {
  if (revision.kind === 'baseline') {
    return (
      <span className="revision-avatar revision-avatar-muted">
        <History size={14} />
      </span>
    )
  }
  if (revision.origin === 'agent') {
    // Same ring colour as the owner's agent in the presence avatars.
    const ring =
      revision.author_id !== null ? { boxShadow: `0 0 0 2px ${colorFor(revision.author_id)}` } : undefined
    return (
      <span className="revision-avatar presence-agent" style={ring}>
        <Sparkles size={14} strokeWidth={2.25} aria-hidden />
      </span>
    )
  }
  const background = revision.author_id !== null ? { background: colorFor(revision.author_id) } : undefined
  if (revision.author_name === null && revision.author_picture_url === null) {
    return (
      <span className="revision-avatar" style={background}>
        <User size={14} />
      </span>
    )
  }
  return (
    <UserAvatar
      className="revision-avatar"
      name={revision.author_name ?? ''}
      pictureUrl={revision.author_picture_url}
      style={background}
    />
  )
}

function RevisionPreview({ detail }: { detail: DiagramRevisionDetail | null }) {
  if (detail === null) {
    return (
      <div className="revision-preview revision-preview-empty">
        <Loader2 size={16} className="spinner" />
      </div>
    )
  }
  if (detail.canvas_state === null) {
    return <div className="revision-preview revision-preview-empty">Empty canvas</div>
  }
  return (
    <div className="revision-preview">
      <TldrawImage
        snapshot={detail.canvas_state as unknown as TLStoreSnapshot}
        shapeUtils={shapeUtils}
        background={false}
        padding={16}
      />
    </div>
  )
}

function detailKey(revision: DiagramRevision): string {
  return `${revision.id}:${revision.updated_at}`
}

export default function HistoryPanel() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const canRestore = useAppStore((state) => state.myRole !== 'viewer')
  const { revisions, isLoading, restore } = useRevisions(activeDiagram?.id ?? null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  // Keyed by id and updated_at: the newest revision keeps changing while someone edits.
  const [details, setDetails] = useState<Record<string, DiagramRevisionDetail>>({})
  const [restoringId, setRestoringId] = useState<string | null>(null)

  async function toggle(revision: DiagramRevision): Promise<void> {
    if (selectedId === revision.id) {
      setSelectedId(null)
      return
    }
    setSelectedId(revision.id)
    if (details[detailKey(revision)] !== undefined) {
      return
    }
    const loaded = await getRevision(revision.diagram_id, revision.id)
    setDetails((current) => ({ ...current, [detailKey(revision)]: loaded }))
  }

  async function handleRestore(revision: DiagramRevision): Promise<void> {
    const confirmed = await confirmDialog({
      title: 'Restore this version?',
      description: `The canvas goes back to how it was ${timeAgo(revision.updated_at)}, for everyone with the diagram open. The current state stays in the history, so this can be undone.`,
      confirmLabel: 'Restore',
    })
    if (!confirmed) {
      return
    }
    setRestoringId(revision.id)
    try {
      await restore(revision)
      setSelectedId(null)
      toast('Version restored', 'success')
    } finally {
      setRestoringId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="full-center" style={{ height: 'auto', padding: 24 }}>
        <Loader2 size={16} className="spinner" /> Loading history…
      </div>
    )
  }
  if (revisions.length === 0) {
    return (
      <EmptyState
        icon={<History size={20} />}
        title="No history yet"
        description="Every change to this diagram, by people or by AI agents, shows up here, and any version can be brought back."
      />
    )
  }

  return (
    <div className="scroll" style={{ flex: 1 }}>
      <ol className="revision-list">
        {revisions.map((revision, index) => {
          const isSelected = selectedId === revision.id
          const isCurrent = index === 0
          return (
            <li key={revision.id} className="revision" data-selected={isSelected}>
              <button
                type="button"
                className="revision-row"
                aria-expanded={isSelected}
                onClick={() => void toggle(revision)}
              >
                <RevisionAvatar revision={revision} />
                <span className="revision-body">
                  <span className="revision-meta">
                    <span className="revision-author">{revisionAuthor(revision)}</span>
                    {revision.origin === 'agent' ? (
                      <span className="revision-badge">
                        <Bot size={11} /> {revision.agent_label ?? 'MCP'}
                      </span>
                    ) : null}
                  </span>
                  <span className="revision-summary">{revisionDescription(revision)}</span>
                  <span className="revision-time" title={new Date(revision.updated_at).toLocaleString()}>
                    {isCurrent ? 'Current · ' : ''}
                    {timeAgo(revision.updated_at)}
                  </span>
                </span>
              </button>
              {isSelected ? (
                <div className="revision-details">
                  <RevisionPreview detail={details[detailKey(revision)] ?? null} />
                  {canRestore && !isCurrent ? (
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={restoringId !== null}
                      onClick={() => void handleRestore(revision)}
                    >
                      {restoringId === revision.id ? (
                        <Loader2 size={13} className="spinner" />
                      ) : (
                        <RotateCcw size={13} />
                      )}{' '}
                      Restore this version
                    </button>
                  ) : null}
                  {!canRestore ? <span className="revision-note">Viewers can't restore versions.</span> : null}
                </div>
              ) : null}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
