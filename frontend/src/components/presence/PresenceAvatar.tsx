import { Sparkles } from 'lucide-react'

import type { PresenceUser } from '../../hooks/useRealtime'
import { colorFor } from '../../utils/avatar'
import { presenceLabel } from '../../utils/presenceLabel'
import UserAvatar from '../ui/UserAvatar'

// A person's photo (or initial on their colour), or an agent's sparkles ringed in its owner's colour.
export default function PresenceAvatar({ user, isYou = false }: { user: PresenceUser; isYou?: boolean }) {
  const label = presenceLabel(user, isYou)
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
