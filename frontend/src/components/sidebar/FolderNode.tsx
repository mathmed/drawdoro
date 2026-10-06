import { ChevronRight, Folder as FolderIcon, FolderOpen, Pencil, Trash2 } from 'lucide-react'

import type { Folder } from '../../api/types'
import { addMenu } from './addMenu'
import DiagramRow from './DiagramRow'
import RowMenu, { INDENT } from './RowMenu'
import type { TreeIndex } from './treeIndex'
import type { TreeActions } from './useTreeActions'

export interface TreeViewProps {
  index: TreeIndex
  expandedFolders: Set<string>
  toggleFolder: (id: string) => void
  activeDiagramId: string | null
  actions: TreeActions
}

// The folders and diagrams directly under a folder (or under the project root when null).
export function TreeChildren({ parentId, depth, ...view }: TreeViewProps & { parentId: string | null; depth: number }) {
  const folders = view.index.folders.get(parentId) ?? []
  const diagrams = view.index.diagrams.get(parentId) ?? []
  return (
    <>
      {folders.map((folder) => (
        <FolderNode key={folder.id} folder={folder} depth={depth} {...view} />
      ))}
      {diagrams.map((diagram) => (
        <DiagramRow
          key={diagram.id}
          diagram={diagram}
          depth={depth}
          isActive={diagram.id === view.activeDiagramId}
          actions={view.actions}
        />
      ))}
    </>
  )
}

export default function FolderNode({ folder, depth, ...view }: TreeViewProps & { folder: Folder; depth: number }) {
  const isExpanded = view.expandedFolders.has(folder.id)
  const isEmpty = !view.index.folders.has(folder.id) && !view.index.diagrams.has(folder.id)
  return (
    <div>
      <div className="tree-row" style={{ paddingLeft: 8 + depth * INDENT }} onClick={() => view.toggleFolder(folder.id)}>
        <span className="tree-chevron" data-open={isExpanded}>
          <ChevronRight size={14} />
        </span>
        {isExpanded ? <FolderOpen size={15} /> : <FolderIcon size={15} />}
        <span className="tree-label">{folder.name}</span>
        <div className="tree-actions">
          <RowMenu label="Add" items={addMenu(view.actions, folder.id)} />
          <RowMenu
            label="More"
            items={[
              { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void view.actions.renameFolder(folder) },
              { kind: 'separator' },
              {
                label: 'Delete',
                icon: <Trash2 size={15} />,
                danger: true,
                onSelect: () => void view.actions.deleteFolder(folder),
              },
            ]}
          />
        </div>
      </div>
      {isExpanded ? (
        <div>
          <TreeChildren parentId={folder.id} depth={depth + 1} {...view} />
          {isEmpty ? (
            <div className="tree-empty" style={{ paddingLeft: 8 + (depth + 1) * INDENT + 18 }}>
              Empty folder
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
