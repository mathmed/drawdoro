import { useAppStore } from '../../store/useAppStore'
import { presenceLabel } from '../../utils/presenceLabel'
import PresenceAvatar from './PresenceAvatar'

const MAX_VISIBLE = 4

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
  const label = people.map((user) => presenceLabel(user, user.id === presence.you)).join(', ')

  return (
    <div className="presence-stack" role="group" aria-label={`In this diagram: ${label}`}>
      {visible.map((user) => (
        <PresenceAvatar key={user.id} user={user} isYou={user.id === presence.you} />
      ))}
      {hidden.length > 0 ? (
        <span className="presence-avatar presence-more" data-tooltip={hidden.map((user) => presenceLabel(user)).join(', ')}>
          +{hidden.length}
        </span>
      ) : null}
    </div>
  )
}
