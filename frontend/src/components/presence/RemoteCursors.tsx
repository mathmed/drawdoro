import { useCallback, useEffect, useMemo, useRef, useSyncExternalStore } from 'react'
import { useValue, type Editor } from 'tldraw'

import { approach, type CanvasPoint, type RemoteCursor, type RemoteCursorStore } from '../../utils/remoteCursors'

const SWEEP_INTERVAL_MS = 1000

interface RemoteCursorsProps {
  editor: Editor
  cursors: RemoteCursorStore
}

// Positions arrive in page coordinates; each frame eases them towards the latest one and converts the
// result to this viewer's screen, so zoom, pan and a different window size all line up. The DOM is
// written directly, so neither the moves nor the animation re-render React.
export default function RemoteCursors({ editor, cursors }: RemoteCursorsProps) {
  const all = useSyncExternalStore(cursors.subscribe, cursors.list)
  const pageId = useValue('remote cursors page', () => editor.getCurrentPageId(), [editor])
  const visible = useMemo(() => all.filter((cursor) => cursor.pageId === pageId), [all, pageId])
  const elements = useRef(new Map<string, HTMLElement>())
  const drawn = useRef(new Map<string, CanvasPoint>())

  const place = useCallback(
    (cursor: RemoteCursor, element: HTMLElement, elapsedMs: number): void => {
      const from = drawn.current.get(cursor.id)
      const point = from === undefined ? cursor.target : approach(from, cursor.target, elapsedMs)
      drawn.current.set(cursor.id, point)
      const screen = editor.pageToViewport(point)
      const transform = `translate(${screen.x}px, ${screen.y}px)`
      if (element.style.transform !== transform) {
        element.style.transform = transform
      }
    },
    [editor],
  )

  useEffect(() => {
    const ids = new Set(visible.map((cursor) => cursor.id))
    for (const id of drawn.current.keys()) {
      if (!ids.has(id)) {
        drawn.current.delete(id)
      }
    }
    if (visible.length === 0) {
      return undefined
    }
    let last = performance.now()
    let frame = requestAnimationFrame(function draw(now: number) {
      const elapsed = now - last
      last = now
      for (const cursor of visible) {
        const element = elements.current.get(cursor.id)
        if (element !== undefined) {
          place(cursor, element, elapsed)
        }
      }
      frame = requestAnimationFrame(draw)
    })
    return () => cancelAnimationFrame(frame)
  }, [place, visible])

  useEffect(() => {
    const timer = setInterval(() => cursors.sweep(Date.now()), SWEEP_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [cursors])

  if (visible.length === 0) {
    return null
  }

  return (
    <div className="remote-cursors" aria-hidden>
      {visible.map((cursor) => (
        <div
          key={cursor.id}
          className="remote-cursor"
          data-cursor-id={cursor.id}
          ref={(element) => {
            if (element === null) {
              elements.current.delete(cursor.id)
              return
            }
            elements.current.set(cursor.id, element)
            place(cursor, element, 0)
          }}
        >
          <svg className="remote-cursor-arrow" width="18" height="18" viewBox="0 0 18 18">
            <path
              d="M2 1.5v13.6l3.8-3.6 2.6 5.6 2.5-1.1-2.6-5.5h5.3z"
              fill={cursor.color}
              stroke="#fff"
              strokeWidth="1.25"
              strokeLinejoin="round"
            />
          </svg>
          <span className="remote-cursor-name" style={{ background: cursor.color }}>
            {cursor.name}
          </span>
        </div>
      ))}
    </div>
  )
}
