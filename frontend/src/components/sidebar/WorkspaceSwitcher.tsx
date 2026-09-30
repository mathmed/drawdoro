import { ChevronsUpDown, Plus, Users } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authConfig } from '../../auth/config'
import { useAppStore } from '../../store/useAppStore'
import { promptDialog } from '../../store/useDialogStore'
import { initial, slugify } from '../../utils/format'
import Menu, { type MenuEntry } from '../ui/Menu'
import MembersDialog from '../workspace/MembersDialog'

export default function WorkspaceSwitcher() {
  const navigate = useNavigate()
  const workspaces = useAppStore((state) => state.workspaces)
  const activeWorkspace = useAppStore((state) => state.activeWorkspace)
  const setActiveWorkspace = useAppStore((state) => state.setActiveWorkspace)
  const createWorkspace = useAppStore((state) => state.createWorkspace)
  const [isMembersOpen, setIsMembersOpen] = useState(false)

  async function handleCreateWorkspace(): Promise<void> {
    const name = await promptDialog({
      title: 'New workspace',
      description: 'Workspaces group projects and the people who work on them.',
      label: 'Name',
      placeholder: 'e.g. Platform Engineering',
    })
    if (name === null) {
      return
    }
    const slug = slugify(name) || `workspace-${Date.now()}`
    await createWorkspace(name, slug)
  }

  const items: MenuEntry[] = [
    { kind: 'label', label: 'Workspaces' },
    ...workspaces.map((workspace) => ({
      label: workspace.name,
      icon: <span className="avatar" style={{ width: 20, height: 20, fontSize: 10.5 }}>{initial(workspace.name)}</span>,
      checked: workspace.id === activeWorkspace?.id,
      onSelect: () => {
        void setActiveWorkspace(workspace)
        navigate('/')
      },
    })),
    { kind: 'separator' },
    ...(authConfig.enabled && activeWorkspace !== null
      ? [{ label: 'Members', icon: <Users size={15} />, onSelect: () => setIsMembersOpen(true) }]
      : []),
    { label: 'New workspace', icon: <Plus size={15} />, onSelect: () => void handleCreateWorkspace() },
  ]

  return (
    <>
      {isMembersOpen ? <MembersDialog onClose={() => setIsMembersOpen(false)} /> : null}
      <Menu
        className="menu-anchor workspace-anchor"
        items={items}
        trigger={({ toggle }) => (
          <button type="button" className="workspace-switcher" onClick={toggle}>
            <span className="avatar">{initial(activeWorkspace?.name)}</span>
            <span className="workspace-switcher-name">{activeWorkspace?.name ?? 'No workspace'}</span>
            <ChevronsUpDown size={14} />
          </button>
        )}
      />
    </>
  )
}
