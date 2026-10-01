import {
  Bot,
  Check,
  Crosshair,
  Eye,
  EyeOff,
  MessageSquare,
  MousePointerClick,
  RotateCcw,
  SendHorizontal,
  Sparkles,
  User,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { TLShapeId } from 'tldraw'

import type { Comment } from '../../api/types'
import { useComments } from '../../hooks/useComments'
import { useAppStore } from '../../store/useAppStore'
import { colorFor } from '../../utils/avatar'
import { commentAuthor, commentResolver, type CommentActorView } from '../../utils/comments'
import { initial, modKey, timeAgo } from '../../utils/format'
import EmptyState from '../ui/EmptyState'

function CommentAvatar({ author }: { author: CommentActorView }) {
  if (author.isAgent) {
    // Same look as the agent in the presence avatars and the history.
    const ring = author.ownerId !== null ? { boxShadow: `0 0 0 2px ${colorFor(author.ownerId)}` } : undefined
    return (
      <div className="comment-avatar presence-agent" style={ring} aria-label={`${author.name} (AI agent)`}>
        <Sparkles size={14} strokeWidth={2.25} aria-hidden />
      </div>
    )
  }
  return <div className="comment-avatar">{author.name !== 'Anonymous' ? initial(author.name) : <User size={14} />}</div>
}

function AgentBadge({ actor }: { actor: CommentActorView }) {
  if (!actor.isAgent) {
    return null
  }
  return (
    <span className="comment-agent-badge" title="Written by an AI agent">
      <Bot size={11} /> {actor.label ?? 'MCP'}
    </span>
  )
}

export default function CommentsPanel() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const activeElementId = useAppStore((state) => state.activeElementId)
  const setActiveElement = useAppStore((state) => state.setActiveElement)
  const editor = useAppStore((state) => state.editor)
  const addComment = useAppStore((state) => state.addComment)
  const setCommentResolved = useAppStore((state) => state.setCommentResolved)
  // Viewers only read; without login (myRole null) everyone can edit.
  const canResolve = useAppStore((state) => state.myRole !== 'viewer')

  const { comments } = useComments(activeDiagram?.id ?? null, activeElementId)
  const [draft, setDraft] = useState('')
  const [selectedShapeId, setSelectedShapeId] = useState<string | null>(null)
  const [showResolved, setShowResolved] = useState(false)
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => {
    if (editor === null) {
      return
    }
    function update(): void {
      if (editor !== null) {
        setSelectedShapeId(editor.getOnlySelectedShapeId())
      }
    }
    update()
    return editor.store.listen(update, { scope: 'session' })
  }, [editor])

  const targetElementId = activeElementId ?? selectedShapeId
  const resolvedCount = comments.filter((comment) => comment.resolved).length
  const visible = showResolved ? comments : comments.filter((comment) => !comment.resolved)

  function shapeLabel(elementId: string): string {
    const shape = editor?.getShape(elementId as TLShapeId)
    if (shape === undefined) {
      return 'Deleted shape'
    }
    return shape.type.charAt(0).toUpperCase() + shape.type.slice(1)
  }

  function focusShape(elementId: string): void {
    if (editor === null) {
      return
    }
    const id = elementId as TLShapeId
    if (editor.getShape(id) === undefined) {
      return
    }
    editor.select(id)
    editor.zoomToSelection({ animation: { duration: 240 } })
  }

  async function handleSend(): Promise<void> {
    const content = draft.trim()
    if (content === '' || targetElementId === null) {
      return
    }
    await addComment(targetElementId, content)
    setDraft('')
  }

  // Failures are already shown by the API client's error toast.
  async function toggleResolved(comment: Comment): Promise<void> {
    setBusyId(comment.id)
    try {
      await setCommentResolved(comment.id, !comment.resolved)
    } finally {
      setBusyId(null)
    }
  }

  function emptyTitle(): string {
    if (resolvedCount > 0) {
      return activeElementId !== null ? 'No open comments on this shape' : 'No open comments'
    }
    return activeElementId !== null ? 'No comments on this shape' : 'No comments yet'
  }

  return (
    <>
      {activeElementId !== null || resolvedCount > 0 ? (
        <div className="panel-toolbar">
          {activeElementId !== null ? (
            <span className="context-chip">
              <Crosshair size={13} /> Showing comments on {shapeLabel(activeElementId).toLowerCase()}
            </span>
          ) : (
            <span className="panel-toolbar-title">
              {comments.length - resolvedCount} open · {resolvedCount} resolved
            </span>
          )}
          <span className="comment-toolbar-actions">
            {resolvedCount > 0 ? (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                aria-pressed={showResolved}
                onClick={() => setShowResolved((value) => !value)}
              >
                {showResolved ? <EyeOff size={13} /> : <Eye size={13} />}
                {showResolved ? 'Hide resolved' : `Show resolved (${resolvedCount})`}
              </button>
            ) : null}
            {activeElementId !== null ? (
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setActiveElement(null)}>
                Show all
              </button>
            ) : null}
          </span>
        </div>
      ) : null}

      <div className="scroll" style={{ flex: 1 }}>
        {visible.length === 0 ? (
          <EmptyState
            icon={<MessageSquare size={20} />}
            title={emptyTitle()}
            description="Select a shape on the canvas — or right-click it and choose Comment — to start a thread."
          />
        ) : (
          <div className="panel-content" style={{ gap: 18 }}>
            {visible.map((comment) => {
              const author = commentAuthor(comment)
              const resolver = commentResolver(comment)
              return (
                <div
                  key={comment.id}
                  className={comment.resolved ? 'comment comment-resolved' : 'comment'}
                  data-testid="comment"
                >
                  <CommentAvatar author={author} />
                  <div className="comment-body">
                    <div className="comment-meta">
                      <span className="comment-author">{author.name}</span>
                      <AgentBadge actor={author} />
                      <span>·</span>
                      <span title={new Date(comment.created_at).toLocaleString()}>{timeAgo(comment.created_at)}</span>
                    </div>
                    {/* Plain text on purpose: comments are never rendered as HTML or Markdown. */}
                    <div className="comment-text">{comment.content}</div>
                    {resolver !== null && comment.resolved_at !== null ? (
                      <div className="comment-resolution">
                        <Check size={12} /> Resolved by {resolver.name}
                        <AgentBadge actor={resolver} />
                        <span title={new Date(comment.resolved_at).toLocaleString()}>
                          · {timeAgo(comment.resolved_at)}
                        </span>
                      </div>
                    ) : null}
                    <div className="comment-actions">
                      {activeElementId === null && comment.element_id !== null ? (
                        <button
                          type="button"
                          className="comment-link"
                          onClick={() => focusShape(comment.element_id ?? '')}
                        >
                          on {shapeLabel(comment.element_id).toLowerCase()} →
                        </button>
                      ) : null}
                      {comment.element_id === null ? <span className="comment-scope">on the diagram</span> : null}
                      {canResolve ? (
                        <button
                          type="button"
                          className="comment-link comment-resolve"
                          disabled={busyId === comment.id}
                          onClick={() => void toggleResolved(comment)}
                        >
                          {comment.resolved ? <RotateCcw size={12} /> : <Check size={12} />}
                          {comment.resolved ? 'Reopen' : 'Resolve'}
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="composer">
        {targetElementId === null ? (
          <span className="context-chip">
            <MousePointerClick size={13} /> Select a shape to comment on it
          </span>
        ) : (
          <span className="context-chip">
            <Crosshair size={13} /> Commenting on {shapeLabel(targetElementId).toLowerCase()}
          </span>
        )}
        <div className="composer-box">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={targetElementId === null ? 'No shape selected' : 'Write a comment…'}
            disabled={targetElementId === null}
            maxLength={5000}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                event.preventDefault()
                void handleSend()
              }
            }}
          />
          <div className="composer-footer">
            <span>{modKey} ↵ to send</span>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => void handleSend()}
              disabled={targetElementId === null || draft.trim() === ''}
            >
              <SendHorizontal size={13} /> Send
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
