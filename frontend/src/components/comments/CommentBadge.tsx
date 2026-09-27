import { useEffect, useState } from 'react'
import type { TLShapeId } from 'tldraw'

import { useAppStore } from '../../store/useAppStore'

interface BadgePosition {
  elementId: string
  count: number
  x: number
  y: number
}

// Overlay drawn on top of the canvas: for every element that has comments it
// places a small badge near the shape's top-right corner, recomputed whenever the
// tldraw store changes (camera panning/zooming, shape edits).
export default function CommentBadge() {
  const editor = useAppStore((state) => state.editor)
  const comments = useAppStore((state) => state.comments)
  const setActiveElement = useAppStore((state) => state.setActiveElement)
  const isCommentsPanelOpen = useAppStore((state) => state.isCommentsPanelOpen)
  const toggleCommentsPanel = useAppStore((state) => state.toggleCommentsPanel)

  const [, forceRender] = useState(0)

  useEffect(() => {
    if (editor === null) {
      return
    }
    const unlisten = editor.store.listen(() => forceRender((value) => value + 1))
    return unlisten
  }, [editor])

  if (editor === null) {
    return null
  }

  const counts = new Map<string, number>()
  for (const comment of comments) {
    counts.set(comment.element_id, (counts.get(comment.element_id) ?? 0) + 1)
  }

  const positions: BadgePosition[] = []
  for (const [elementId, count] of counts) {
    const bounds = editor.getShapePageBounds(elementId as TLShapeId)
    if (bounds === undefined) {
      continue
    }
    const point = editor.pageToViewport({ x: bounds.maxX, y: bounds.minY })
    positions.push({ elementId, count, x: point.x, y: point.y })
  }

  function handleClick(elementId: string): void {
    setActiveElement(elementId)
    if (!isCommentsPanelOpen) {
      toggleCommentsPanel()
    }
  }

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 200,
        overflow: 'hidden',
      }}
    >
      {positions.map((position) => (
        <button
          key={position.elementId}
          type="button"
          onClick={() => handleClick(position.elementId)}
          style={{
            position: 'absolute',
            left: position.x - 10,
            top: position.y - 10,
            pointerEvents: 'auto',
            background: '#db6d28',
            color: '#0f1117',
            border: '1px solid #0f1117',
            borderRadius: 12,
            minWidth: 20,
            height: 20,
            padding: '0 6px',
            fontSize: 11,
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          💬 {position.count}
        </button>
      ))}
    </div>
  )
}
