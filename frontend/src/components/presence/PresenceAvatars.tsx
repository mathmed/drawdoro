import { Sparkles } from 'lucide-react'

import type { PresenceUser } from '../../hooks/useRealtime'
import { useAppStore } from '../../store/useAppStore'
import { agentDescription } from '../../utils/agents'
import { colorFor } from '../../utils/avatar'
import UserAvatar from '../ui/UserAvatar'

const MAX_VISIBLE = 4

function labelFor(user: PresenceUser, isYou: boolean): string {
  if (user.kind === 'agent') {
    return agentDescription({ name: user.name, ownerName: user.owner_name, label: user.label })
  }
  return isYou ? `${user.name} (you)` : user.name
}

function Avatar({ user, isYou }: { user: PresenceUser; isYou: boolean }) {
  const label = labelFor(user, isYou)
  if (user.kind === 'agent') {
    return (
      <span
        className="presence-avatar presence-agent"
        // Each owner's agent gets its own ring colour, so two people's agents are told apart.
        style={user.owner_id ? { boxShadow: `0 0 0 2px ${colorFor(user.owner_id)}` } : undefined}
        data-tooltip={label}
        aria-label={label}
      >
        <Sparkles size={14} strokeWidth={2.25} aria-hidden />
      </span>
    )
  }
  return (
    <span className="presence-avatar" data-you={isYou} data-tooltip={label} aria-label={label}>
      <UserAvatar
        className="presence-avatar-face"
        name={user.name}
        pictureUrl={user.picture_url}
        style={{ background: colorFor(user.id) }}
      />
    </span>
  )
}

// Everyone in this diagram, the local user first.
export default function PresenceAvatars() {
  const presence = useAppStore((state) => state.presence)
  const you = presence.users.filter((user) => user.id === presence.you)
  const people = [...you, ...presence.users.filter((user) => user.id !== presence.you)]

  if (people.length === 0) {
    return null
  }
  const visible = people.slice(0, MAX_VISIBLE)
  const hidden = people.slice(MAX_VISIBLE)
  const label = people.map((user) => labelFor(user, user.id === presence.you)).join(', ')

  return (
    <div className="presence-stack" role="group" aria-label={`In this diagram: ${label}`}>
      {visible.map((user) => (
        <Avatar key={user.id} user={user} isYou={user.id === presence.you} />
      ))}
      {hidden.length > 0 ? (
        <span className="presence-avatar presence-more" data-tooltip={hidden.map((user) => labelFor(user, false)).join(', ')}>
          +{hidden.length}
        </span>
      ) : null}
    </div>
  )
}
