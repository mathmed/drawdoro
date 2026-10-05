import { memo, useMemo } from 'react'

import type { PresenceUser } from '../../hooks/useRealtime'
import { useAppStore } from '../../store/useAppStore'
import { useDiagramPresence, useProjectPresence, useWorkspacePresenceStore } from '../../store/useWorkspacePresenceStore'
import { presenceLabel } from '../../utils/presenceLabel'
import { othersThan } from '../../utils/workspacePresence'
import PresenceAvatar from '../presence/PresenceAvatar'

export const SIDEBAR_MAX_AVATARS = 3

// This person is left out everywhere in the sidebar (the top bar already shows them in the open
// diagram): the workspace channel names their account, the diagram channel their tab when login is off.
function useOthers(users: PresenceUser[]): PresenceUser[] {
  const you = useWorkspacePresenceStore((state) => state.you)
  const thisTab = useAppStore((state) => state.presence.you)
  return useMemo(() => othersThan(users, [you, thisTab]), [users, you, thisTab])
}

function PresenceStack({ users, place }: { users: PresenceUser[]; place: string }) {
  const others = useOthers(users)
  if (others.length === 0) {
    return null
  }
  const visible = others.slice(0, SIDEBAR_MAX_AVATARS)
  const hidden = others.slice(SIDEBAR_MAX_AVATARS)
  const names = others.map((user) => presenceLabel(user)).join(', ')
  return (
    <div className="presence-stack sidebar-presence" role="group" aria-label={`In this ${place} now: ${names}`}>
      {visible.map((user) => (
        <PresenceAvatar key={user.id} user={user} />
      ))}
      {hidden.length > 0 ? (
        <span
          className="presence-avatar presence-more"
          data-tooltip={hidden.map((user) => presenceLabel(user)).join(', ')}
          aria-label={`${hidden.length} more: ${hidden.map((user) => presenceLabel(user)).join(', ')}`}
        >
          +{hidden.length}
        </span>
      ) : null}
    </div>
  )
}

export const DiagramPresence = memo(function DiagramPresence({ diagramId }: { diagramId: string }) {
  return <PresenceStack users={useDiagramPresence(diagramId)} place="diagram" />
})

// Everyone in any diagram of the project, each once, shown even while the project is collapsed.
export const ProjectPresence = memo(function ProjectPresence({ projectId }: { projectId: string }) {
  return <PresenceStack users={useProjectPresence(projectId)} place="project" />
})
