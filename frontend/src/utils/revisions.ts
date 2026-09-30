import type { DiagramRevision } from '../api/types'
import { agentDisplayName } from './agents'

export function revisionAuthor(revision: DiagramRevision): string {
  if (revision.kind === 'baseline') {
    return 'Earlier version'
  }
  if (revision.origin === 'agent') {
    return agentDisplayName({ name: revision.agent_name ?? 'AI agent', ownerName: revision.author_name })
  }
  return revision.author_name ?? 'Someone'
}

export function revisionDescription(revision: DiagramRevision): string {
  if (revision.kind === 'baseline') {
    return 'State before the recorded changes'
  }
  if (revision.kind === 'restore') {
    return revision.summary ?? 'Restored an earlier version'
  }
  return revision.summary ?? (revision.origin === 'agent' ? 'Changed the diagram' : 'Edited the diagram')
}
