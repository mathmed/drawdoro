import { MessageSquare } from 'lucide-react'
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
// places a small pin near the shape's top-right corner, recomputed whenever the
// tldraw store changes (camera panning/zooming, shape edits).
export default function CommentBadge() {
  const editor = useAppStore((state) => state.editor)
  const comments = useAppStore((state) => state.comments)
  const commentOnElement = useAppStore((state) => state.commentOnElement)

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

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 200, overflow: 'hidden' }}>
      {positions.map((position) => (
        <button
          key={position.elementId}
          type="button"
          className="comment-pin"
          aria-label={`${position.count} comment${position.count === 1 ? '' : 's'}`}
          onClick={() => commentOnElement(position.elementId)}
          style={{ left: position.x, top: position.y }}
        >
          <MessageSquare size={11} strokeWidth={2.5} />
          {position.count}
        </button>
      ))}
    </div>
  )
}
