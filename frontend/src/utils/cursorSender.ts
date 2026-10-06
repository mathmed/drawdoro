import type { CursorPosition } from './remoteCursors'

// ~30 messages a second: smooth enough once eased on the other side, light on the socket.
export const CURSOR_SEND_INTERVAL_MS = 33

export interface CursorSender {
  update: (position: CursorPosition | null) => void
  dispose: () => void
}

// A tenth of a page unit is below a pixel at any usable zoom, and keeps the messages short.
function rounded(position: CursorPosition | null): CursorPosition | null {
  if (position === null) {
    return null
  }
  const round = (value: number): number => Math.round(value * 10) / 10
  return { point: { x: round(position.point.x), y: round(position.point.y) }, page: position.page }
}

function keyOf(position: CursorPosition | null): string {
  return position === null ? 'away' : `${position.page} ${position.point.x} ${position.point.y}`
}

// Coalesces pointer moves into at most one message per interval, always ending on the latest
// position, and never sends a position the others already have.
export function createCursorSender(
  send: (position: CursorPosition | null) => void,
  intervalMs: number = CURSOR_SEND_INTERVAL_MS,
): CursorSender {
  let lastSentAt = Number.NEGATIVE_INFINITY
  let lastSentKey: string | null = null
  let latest: CursorPosition | null = null
  let timer: ReturnType<typeof setTimeout> | null = null

  function flush(): void {
    timer = null
    const position = rounded(latest)
    const key = keyOf(position)
    if (key === lastSentKey) {
      return
    }
    lastSentKey = key
    lastSentAt = Date.now()
    send(position)
  }

  return {
    update(position) {
      latest = position
      if (timer !== null) {
        return
      }
      const wait = lastSentAt + intervalMs - Date.now()
      if (wait <= 0) {
        flush()
        return
      }
      timer = setTimeout(flush, wait)
    },
    dispose() {
      if (timer !== null) {
        clearTimeout(timer)
      }
      timer = null
    },
  }
}
