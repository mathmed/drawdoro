import { useState } from 'react'

import { useComments } from '../../hooks/useComments'
import { useAppStore } from '../../store/useAppStore'

export default function CommentsPanel() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const activeElementId = useAppStore((state) => state.activeElementId)
  const setActiveElement = useAppStore((state) => state.setActiveElement)
  const toggleCommentsPanel = useAppStore((state) => state.toggleCommentsPanel)
  const editor = useAppStore((state) => state.editor)
  const addComment = useAppStore((state) => state.addComment)

  const { comments } = useComments(activeDiagram?.id ?? null, activeElementId)
  const [draft, setDraft] = useState('')

  const targetElementId =
    activeElementId ?? (editor !== null ? editor.getOnlySelectedShapeId() : null)

  async function handleSend(): Promise<void> {
    const content = draft.trim()
    if (content === '' || targetElementId === null) {
      return
    }
    await addComment(targetElementId, content)
    setDraft('')
  }

  return (
    <aside
      style={{
        width: 300,
        flexShrink: 0,
        height: '100%',
        background: '#161b22',
        borderLeft: '1px solid #30363d',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 12px',
          borderBottom: '1px solid #30363d',
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        <span>💬 Comments</span>
        <button
          type="button"
          onClick={toggleCommentsPanel}
          style={{
            background: 'transparent',
            color: '#8b949e',
            border: 'none',
            cursor: 'pointer',
            fontSize: 14,
          }}
        >
          ✕
        </button>
      </header>

      {activeElementId !== null ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 12px',
            borderBottom: '1px solid #30363d',
            fontSize: 12,
            color: '#8b949e',
          }}
        >
          <span>On element: {activeElementId.slice(0, 12)}…</span>
          <button
            type="button"
            onClick={() => setActiveElement(null)}
            style={{
              background: 'transparent',
              color: '#2f81f7',
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            show all
          </button>
        </div>
      ) : null}

      <div style={{ flex: 1, overflow: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {comments.length === 0 ? (
          <div style={{ color: '#8b949e', fontSize: 13 }}>No comments yet.</div>
        ) : (
          comments.map((comment) => (
            <div
              key={comment.id}
              style={{
                background: '#0f1117',
                border: '1px solid #30363d',
                borderRadius: 8,
                padding: 8,
              }}
            >
              <div style={{ fontSize: 13, color: '#e6edf3', whiteSpace: 'pre-wrap' }}>
                {comment.content}
              </div>
              <div style={{ fontSize: 11, color: '#8b949e', marginTop: 4 }}>
                {new Date(comment.created_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>

      <div style={{ borderTop: '1px solid #30363d', padding: 12 }}>
        {targetElementId === null ? (
          <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 6 }}>
            Select an element to comment on it.
          </div>
        ) : null}
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Write a comment…"
          disabled={targetElementId === null}
          style={{
            width: '100%',
            boxSizing: 'border-box',
            resize: 'vertical',
            minHeight: 60,
            background: '#0f1117',
            color: '#e6edf3',
            border: '1px solid #30363d',
            borderRadius: 6,
            padding: 8,
            fontSize: 13,
          }}
        />
        <button
          type="button"
          onClick={() => void handleSend()}
          disabled={targetElementId === null || draft.trim() === ''}
          style={{
            marginTop: 8,
            width: '100%',
            background: '#2f81f7',
            color: '#e6edf3',
            border: '1px solid #30363d',
            borderRadius: 6,
            padding: '6px 12px',
            fontSize: 13,
            cursor: targetElementId === null ? 'default' : 'pointer',
            opacity: targetElementId === null || draft.trim() === '' ? 0.6 : 1,
          }}
        >
          Comment
        </button>
      </div>
    </aside>
  )
}
