import { Crosshair, MessageSquare, MousePointerClick, SendHorizontal, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { TLShapeId } from 'tldraw'

import { useComments } from '../../hooks/useComments'
import { useAppStore } from '../../store/useAppStore'
import { initial, modKey, timeAgo } from '../../utils/format'
import EmptyState from '../ui/EmptyState'

export default function CommentsPanel() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const activeElementId = useAppStore((state) => state.activeElementId)
  const setActiveElement = useAppStore((state) => state.setActiveElement)
  const editor = useAppStore((state) => state.editor)
  const addComment = useAppStore((state) => state.addComment)

  const { comments } = useComments(activeDiagram?.id ?? null, activeElementId)
  const [draft, setDraft] = useState('')
  const [selectedShapeId, setSelectedShapeId] = useState<string | null>(null)

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

  return (
    <>
      {activeElementId !== null ? (
        <div className="panel-toolbar">
          <span className="context-chip">
            <Crosshair size={13} /> Showing comments on {shapeLabel(activeElementId).toLowerCase()}
          </span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setActiveElement(null)}>
            Show all
          </button>
        </div>
      ) : null}

      <div className="scroll" style={{ flex: 1 }}>
        {comments.length === 0 ? (
          <EmptyState
            icon={<MessageSquare size={20} />}
            title={activeElementId !== null ? 'No comments on this shape' : 'No comments yet'}
            description="Select a shape on the canvas — or right-click it and choose Comment — to start a thread."
          />
        ) : (
          <div className="panel-content" style={{ gap: 18 }}>
            {comments.map((comment) => (
              <div key={comment.id} className="comment">
                <div className="comment-avatar">
                  {comment.author_name !== null ? initial(comment.author_name) : <User size={14} />}
                </div>
                <div className="comment-body">
                  <div className="comment-meta">
                    <span className="comment-author">{comment.author_name ?? 'Anonymous'}</span>
                    <span>·</span>
                    <span title={new Date(comment.created_at).toLocaleString()}>{timeAgo(comment.created_at)}</span>
                  </div>
                  <div className="comment-text">{comment.content}</div>
                  {activeElementId === null ? (
                    <button type="button" className="comment-link" onClick={() => focusShape(comment.element_id)}>
                      on {shapeLabel(comment.element_id).toLowerCase()} →
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
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
