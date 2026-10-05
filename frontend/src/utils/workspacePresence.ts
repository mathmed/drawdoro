import type { PresenceUser } from '../hooks/useRealtime'

// Who is in one diagram of the workspace right now, as the server reports it. No users means nobody.
export interface DiagramPresenceUpdate {
  diagramId: string
  projectId: string
  users: PresenceUser[]
}

export type WorkspacePresenceMessage =
  | { type: 'presence_snapshot'; you: string | null; diagrams: DiagramPresenceUpdate[] }
  | { type: 'presence_delta'; diagrams: DiagramPresenceUpdate[] }

export interface DiagramPresence {
  projectId: string
  users: PresenceUser[]
}

// Kept per diagram and per project (the people of all its diagrams, each once). Entries that did not
// change keep their reference, so only the sidebar rows whose people changed render again.
export interface PresenceIndex {
  byDiagram: Record<string, DiagramPresence>
  byProject: Record<string, PresenceUser[]>
}

export const EMPTY_PRESENCE_INDEX: PresenceIndex = { byDiagram: {}, byProject: {} }

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isOptionalString(value: unknown): value is string | undefined {
  return value === undefined || typeof value === 'string'
}

function parseUser(value: unknown): PresenceUser | null {
  if (!isRecord(value) || typeof value.id !== 'string' || typeof value.name !== 'string') {
    return null
  }
  const { kind, picture_url: pictureUrl, owner_id: ownerId, owner_name: ownerName, label } = value
  if (kind !== undefined && kind !== 'person' && kind !== 'agent') {
    return null
  }
  if (pictureUrl !== null && !isOptionalString(pictureUrl)) {
    return null
  }
  if (!isOptionalString(ownerId) || !isOptionalString(ownerName) || !isOptionalString(label)) {
    return null
  }
  return { id: value.id, name: value.name, kind, picture_url: pictureUrl, owner_id: ownerId, owner_name: ownerName, label }
}

function parseDiagram(value: unknown): DiagramPresenceUpdate | null {
  if (!isRecord(value) || typeof value.diagram_id !== 'string' || typeof value.project_id !== 'string') {
    return null
  }
  if (!Array.isArray(value.users)) {
    return null
  }
  const users = value.users.map(parseUser)
  if (users.some((user) => user === null)) {
    return null
  }
  return { diagramId: value.diagram_id, projectId: value.project_id, users: users as PresenceUser[] }
}

// Anything that is not a well-formed snapshot or delta (an older or newer server, a bad frame) is
// ignored as a whole, so the sidebar never shows half of a message.
export function parseWorkspacePresenceMessage(message: unknown): WorkspacePresenceMessage | null {
  if (!isRecord(message) || !Array.isArray(message.diagrams)) {
    return null
  }
  const diagrams = message.diagrams.map(parseDiagram)
  if (diagrams.some((diagram) => diagram === null)) {
    return null
  }
  const parsed = diagrams as DiagramPresenceUpdate[]
  if (message.type === 'presence_delta') {
    return { type: 'presence_delta', diagrams: parsed }
  }
  if (message.type !== 'presence_snapshot' || (message.you !== null && typeof message.you !== 'string')) {
    return null
  }
  return { type: 'presence_snapshot', you: message.you, diagrams: parsed }
}

function sameUser(a: PresenceUser, b: PresenceUser): boolean {
  return (
    a.id === b.id &&
    a.name === b.name &&
    a.kind === b.kind &&
    (a.picture_url ?? null) === (b.picture_url ?? null) &&
    a.owner_id === b.owner_id &&
    a.owner_name === b.owner_name &&
    a.label === b.label
  )
}

export function sameUsers(a: PresenceUser[] | undefined, b: PresenceUser[]): boolean {
  return a !== undefined && a.length === b.length && a.every((user, index) => sameUser(user, b[index]))
}

// People by name, then agents by name, like the presence of a single diagram.
function byKindThenName(a: PresenceUser, b: PresenceUser): number {
  const kind = Number(a.kind === 'agent') - Number(b.kind === 'agent')
  return kind !== 0 ? kind : a.name.localeCompare(b.name) || a.id.localeCompare(b.id)
}

function unionOf(diagrams: DiagramPresence[]): PresenceUser[] {
  const unique = new Map<string, PresenceUser>()
  for (const diagram of diagrams) {
    for (const user of diagram.users) {
      if (!unique.has(user.id)) {
        unique.set(user.id, user)
      }
    }
  }
  return [...unique.values()].sort(byKindThenName)
}

// A snapshot replaces everything; a delta replaces only the diagrams it lists. Either way only the
// projects of the diagrams that changed are recomputed.
export function applyPresence(index: PresenceIndex, updates: DiagramPresenceUpdate[], replace: boolean): PresenceIndex {
  const byDiagram: Record<string, DiagramPresence> = replace ? {} : { ...index.byDiagram }
  const touched = new Set<string>(replace ? Object.keys(index.byProject) : [])
  for (const update of updates) {
    const previous = index.byDiagram[update.diagramId]
    if (previous !== undefined) {
      touched.add(previous.projectId)
      delete byDiagram[update.diagramId]
    }
    if (update.users.length === 0) {
      continue
    }
    touched.add(update.projectId)
    const unchanged = previous?.projectId === update.projectId && sameUsers(previous.users, update.users)
    byDiagram[update.diagramId] = unchanged ? previous : { projectId: update.projectId, users: update.users }
  }

  const byProject: Record<string, PresenceUser[]> = { ...index.byProject }
  for (const projectId of touched) {
    const union = unionOf(Object.values(byDiagram).filter((diagram) => diagram.projectId === projectId))
    if (union.length === 0) {
      delete byProject[projectId]
    } else if (!sameUsers(index.byProject[projectId], union)) {
      byProject[projectId] = union
    }
  }
  return { byDiagram, byProject }
}

// The sidebar shows where the other people are: this person (from any of their tabs) is left out.
export function othersThan(users: PresenceUser[], selfIds: ReadonlyArray<string | null>): PresenceUser[] {
  return users.filter((user) => !selfIds.includes(user.id))
}
