import { ChevronRight, Layers, Pencil, Trash2 } from 'lucide-react'

import type { Project } from '../../api/types'
import LoadingGate from '../ui/loading/LoadingGate'
import { addMenu, TreeChildren, type TreeViewProps } from './FolderNode'
import RowMenu, { INDENT } from './RowMenu'
import TreeSkeleton from './TreeSkeleton'

interface ProjectNodeProps {
  project: Project
  isActive: boolean
  isExpanded: boolean
  isLoading: boolean
  onSelect: (project: Project) => void
  // Only the active project has its tree loaded; the others render just their row.
  view: TreeViewProps
}

export default function ProjectNode({ project, isActive, isExpanded, isLoading, onSelect, view }: ProjectNodeProps) {
  const isEmpty = view.index.folders.size === 0 && view.index.diagrams.size === 0
  return (
    <div>
      <div className="tree-row" data-strong={isActive} style={{ paddingLeft: 8 }} onClick={() => onSelect(project)}>
        <span className="tree-chevron" data-open={isExpanded}>
          <ChevronRight size={14} />
        </span>
        <Layers size={15} />
        <span className="tree-label">{project.name}</span>
        <div className="tree-actions">
          {isActive ? <RowMenu label="Add" items={addMenu(view.actions)} /> : null}
          <RowMenu
            label="More"
            items={[
              { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void view.actions.renameProject(project) },
              { kind: 'separator' },
              {
                label: 'Delete project',
                icon: <Trash2 size={15} />,
                danger: true,
                onSelect: () => void view.actions.deleteProject(project),
              },
            ]}
          />
        </div>
      </div>
      {isExpanded ? (
        <div>
          <LoadingGate loading={isEmpty && isLoading} fallback={<TreeSkeleton />}>
            <TreeChildren parentId={null} depth={1} {...view} />
            {isEmpty ? (
              <div className="tree-empty" style={{ paddingLeft: 8 + INDENT + 18 }}>
                No diagrams yet ·{' '}
                <button type="button" onClick={() => view.actions.newDiagram()}>
                  Create one
                </button>
              </div>
            ) : null}
          </LoadingGate>
        </div>
      ) : null}
    </div>
  )
}
