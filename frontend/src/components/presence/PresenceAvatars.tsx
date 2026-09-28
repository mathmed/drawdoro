import type { PresenceUser } from '../../hooks/useRealtime'
import { useAppStore } from '../../store/useAppStore'
import { initial } from '../../utils/format'

const MAX_VISIBLE = 4

// Stable colour per person so the same collaborator always looks the same.
function colorFor(id: string): string {
  let hash = 2166136261
  for (const char of id) {
    hash = Math.imul(hash ^ char.charCodeAt(0), 16777619) >>> 0
  }
  // The golden angle spreads hues apart even for near-identical ids.
  return `hsl(${Math.round((hash * 137.508) % 360)} 62% 50%)`
}

function Avatar({ user, isYou }: { user: PresenceUser; isYou: boolean }) {
  const label = isYou ? `${user.name} (you)` : user.name
  return (
    <span
      className="presence-avatar"
      data-you={isYou}
      style={{ background: colorFor(user.id) }}
      data-tooltip={label}
      aria-label={label}
    >
      {initial(user.name)}
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
  const label = people.map((user) => (user.id === presence.you ? `${user.name} (you)` : user.name)).join(', ')

  return (
    <div className="presence-stack" role="group" aria-label={`In this diagram: ${label}`}>
      {visible.map((user) => (
        <Avatar key={user.id} user={user} isYou={user.id === presence.you} />
      ))}
      {hidden.length > 0 ? (
        <span className="presence-avatar presence-more" data-tooltip={hidden.map((user) => user.name).join(', ')}>
          +{hidden.length}
        </span>
      ) : null}
    </div>
  )
}
