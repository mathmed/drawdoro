import { LogOut, Trash2, UserPlus } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import type { WorkspaceRole } from '../../api/types'
import { branding } from '../../config/branding'
import { useAppStore } from '../../store/useAppStore'
import { useAuthStore } from '../../store/useAuthStore'
import { confirmDialog } from '../../store/useDialogStore'
import { initial } from '../../utils/format'
import Modal from '../ui/Modal'

const ROLES: { value: WorkspaceRole; label: string; description: string }[] = [
  { value: 'owner', label: 'Owner', description: 'Manages members and the workspace' },
  { value: 'editor', label: 'Editor', description: 'Creates and edits diagrams' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access' },
]

export default function MembersDialog({ onClose }: { onClose: () => void }) {
  const workspace = useAppStore((state) => state.activeWorkspace)
  const members = useAppStore((state) => state.members)
  const myRole = useAppStore((state) => state.myRole)
  const addMember = useAppStore((state) => state.addMember)
  const updateMemberRole = useAppStore((state) => state.updateMemberRole)
  const removeMember = useAppStore((state) => state.removeMember)
  const myEmail = useAuthStore((state) => state.profile?.email.toLowerCase())

  const [email, setEmail] = useState('')
  const [role, setRole] = useState<WorkspaceRole>('editor')
  const [isAdding, setIsAdding] = useState(false)
  const isOwner = myRole === 'owner'

  async function handleAdd(event: FormEvent): Promise<void> {
    event.preventDefault()
    if (email.trim() === '') {
      return
    }
    setIsAdding(true)
    try {
      await addMember(email.trim(), role)
      setEmail('')
    } finally {
      setIsAdding(false)
    }
  }

  async function handleRemove(userId: string, name: string, isMe: boolean): Promise<void> {
    const confirmed = await confirmDialog({
      title: isMe ? `Leave “${workspace?.name}”?` : `Remove ${name}?`,
      description: isMe
        ? 'You will lose access to this workspace until an owner adds you again.'
        : `${name} will lose access to this workspace.`,
      confirmLabel: isMe ? 'Leave workspace' : 'Remove member',
      danger: true,
    })
    if (!confirmed) {
      return
    }
    await removeMember(userId)
    if (isMe) {
      onClose()
    }
  }

  return (
    <Modal
      title="Members"
      description={`People with access to ${workspace?.name ?? 'this workspace'}.`}
      size="lg"
      onClose={onClose}
    >
      {isOwner ? (
        <form className="member-add" onSubmit={(event) => void handleAdd(event)}>
          <input
            className="input"
            type="email"
            placeholder="name@condoconta.com.br"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-label="Email"
          />
          <select className="select" value={role} onChange={(event) => setRole(event.target.value as WorkspaceRole)} aria-label="Role">
            {ROLES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <button type="submit" className="btn btn-primary" disabled={isAdding || email.trim() === ''}>
            <UserPlus size={15} /> Add
          </button>
        </form>
      ) : null}
      {isOwner ? <p className="field-hint">People need to sign in to {branding.name} once before they can be added.</p> : null}

      <ul className="member-list">
        {members.map((member) => {
          const isMe = member.email === myEmail
          return (
            <li key={member.user_id} className="member-row">
              <span className="user-avatar">{initial(member.name)}</span>
              <div className="member-info">
                <span className="member-name">
                  {member.name}
                  {isMe ? <span className="member-you">you</span> : null}
                </span>
                <span className="member-email">{member.email}</span>
              </div>
              {isOwner ? (
                <select
                  className="select member-role"
                  value={member.role}
                  aria-label={`Role of ${member.name}`}
                  onChange={(event) => void updateMemberRole(member.user_id, event.target.value as WorkspaceRole)}
                >
                  {ROLES.map((item) => (
                    <option key={item.value} value={item.value} title={item.description}>
                      {item.label}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="badge badge-neutral">{member.role}</span>
              )}
              {isOwner || isMe ? (
                <button
                  type="button"
                  className="btn btn-ghost btn-icon btn-sm"
                  aria-label={isMe ? 'Leave workspace' : `Remove ${member.name}`}
                  title={isMe ? 'Leave workspace' : 'Remove member'}
                  onClick={() => void handleRemove(member.user_id, member.name, isMe)}
                >
                  {isMe ? <LogOut size={15} /> : <Trash2 size={15} />}
                </button>
              ) : null}
            </li>
          )
        })}
      </ul>
    </Modal>
  )
}
