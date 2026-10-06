import type { PresenceUser } from '../hooks/useRealtime'
import { agentDescription } from './agents'

// How a presence entry is named in tooltips and labels: a person by name, an agent as its owner's agent.
export function presenceLabel(user: PresenceUser, isYou = false): string {
  if (user.kind === 'agent') {
    return agentDescription({ name: user.name, ownerName: user.owner_name, label: user.label })
  }
  return isYou ? `${user.name} (you)` : user.name
}
