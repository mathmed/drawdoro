import { FilePlus2, FolderPlus } from 'lucide-react'

import type { MenuEntry } from '../ui/Menu'
import type { TreeActions } from './useTreeActions'

export function addMenu(actions: TreeActions, folderId?: string): MenuEntry[] {
  return [
    { label: 'New diagram', icon: <FilePlus2 size={15} />, onSelect: () => actions.newDiagram(folderId) },
    { label: 'New folder', icon: <FolderPlus size={15} />, onSelect: () => void actions.createFolder(folderId) },
  ]
}
