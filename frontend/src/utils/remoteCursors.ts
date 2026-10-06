import { colorFor } from './avatar'

export interface CanvasPoint {
  x: number
  y: number
}

// Where a pointer is on the canvas: page coordinates, so each viewer draws it at their own zoom and pan.
export interface CursorPosition {
  point: CanvasPoint
  page: string
}

// What the server relays when someone moves their pointer, stamped with their presence id and name.
// A null point means the pointer left the canvas.
export interface CursorMessage {
  id: string
  name: string
  point: CanvasPoint | null
  page: string | null
}

export interface RemoteCursor {
  id: string
  name: string
  color: string
  pageId: string
  target: CanvasPoint
  lastSeenAt: number
}

// Someone whose pointer has not moved for this long is treated as away and their cursor hidden.
export const CURSOR_INACTIVE_MS = 30_000
// How quickly a drawn cursor catches up with the latest position (time constant of the easing).
export const CURSOR_SMOOTHING_MS = 50
// Closer than this (in page units) the cursor simply lands on its target.
const SNAP_DISTANCE = 0.05

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isCoordinate(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function parsePoint(value: unknown): CanvasPoint | null | undefined {
  if (value === null) {
    return null
  }
  if (!isRecord(value) || !isCoordinate(value.x) || !isCoordinate(value.y)) {
    return undefined
  }
  return { x: value.x, y: value.y }
}

// Anything that is not a well-formed cursor (an older or newer server, a bad frame) is ignored.
export function parseCursorMessage(message: unknown): CursorMessage | null {
  if (!isRecord(message) || typeof message.id !== 'string' || typeof message.name !== 'string') {
    return null
  }
  const point = parsePoint(message.point)
  if (point === undefined) {
    return null
  }
  if (point === null) {
    return { id: message.id, name: message.name, point: null, page: null }
  }
  if (typeof message.page !== 'string') {
    return null
  }
  return { id: message.id, name: message.name, point, page: message.page }
}

export function approach(from: CanvasPoint, to: CanvasPoint, elapsedMs: number): CanvasPoint {
  if (Math.hypot(to.x - from.x, to.y - from.y) < SNAP_DISTANCE) {
    return to
  }
  const progress = 1 - Math.exp(-Math.max(elapsedMs, 0) / CURSOR_SMOOTHING_MS)
  return { x: from.x + (to.x - from.x) * progress, y: from.y + (to.y - from.y) * progress }
}

// The other people's cursors in one diagram. Subscribers hear only when someone appears, disappears,
// changes page or name; moves just update the target, which the overlay reads on every frame, so a
// moving pointer never re-renders React.
export class RemoteCursorStore {
  private readonly cursors = new Map<string, RemoteCursor>()
  private readonly listeners = new Set<() => void>()
  private snapshot: RemoteCursor[] = []

  apply(message: CursorMessage, now: number): void {
    if (message.point === null || message.page === null) {
      this.remove(message.id)
      return
    }
    const existing = this.cursors.get(message.id)
    if (existing !== undefined && existing.name === message.name && existing.pageId === message.page) {
      existing.target = message.point
      existing.lastSeenAt = now
      return
    }
    this.cursors.set(message.id, {
      id: message.id,
      name: message.name,
      color: colorFor(message.id),
      pageId: message.page,
      target: message.point,
      lastSeenAt: now,
    })
    this.changed()
  }

  // Drops the cursors of people who are no longer in the diagram.
  retain(ids: ReadonlySet<string>): void {
    this.removeWhere((cursor) => !ids.has(cursor.id))
  }

  sweep(now: number): void {
    this.removeWhere((cursor) => now - cursor.lastSeenAt >= CURSOR_INACTIVE_MS)
  }

  clear(): void {
    this.removeWhere(() => true)
  }

  remove(id: string): void {
    if (this.cursors.delete(id)) {
      this.changed()
    }
  }

  readonly list = (): RemoteCursor[] => this.snapshot

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private removeWhere(predicate: (cursor: RemoteCursor) => boolean): void {
    const gone = this.snapshot.filter(predicate)
    if (gone.length === 0) {
      return
    }
    for (const cursor of gone) {
      this.cursors.delete(cursor.id)
    }
    this.changed()
  }

  private changed(): void {
    this.snapshot = [...this.cursors.values()]
    for (const listener of this.listeners) {
      listener()
    }
  }
}
