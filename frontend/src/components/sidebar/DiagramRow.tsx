import { Pencil, Trash2, Workflow } from 'lucide-react'
import { memo } from 'react'
import { useNavigate } from 'react-router-dom'

import type { DiagramSummary } from '../../api/types'
import RowMenu, { INDENT } from './RowMenu'
import { DiagramPresence } from './SidebarPresence'
import type { TreeActions } from './useTreeActions'

interface DiagramRowProps {
  diagram: DiagramSummary
  depth: number
  isActive: boolean
  actions: TreeActions
}

function DiagramRow({ diagram, depth, isActive, actions }: DiagramRowProps) {
  const navigate = useNavigate()
  return (
    <div
      className="tree-row"
      data-active={isActive}
      style={{ paddingLeft: 8 + depth * INDENT + 18 }}
      onClick={() => navigate(`/diagrams/${diagram.id}`)}
    >
      <Workflow size={15} />
      <span className="tree-label">{diagram.name}</span>
      <DiagramPresence diagramId={diagram.id} />
      <div className="tree-actions">
        <RowMenu
          label="More"
          items={[
            { label: 'Rename', icon: <Pencil size={15} />, onSelect: () => void actions.renameDiagram(diagram) },
            { kind: 'separator' },
            {
              label: 'Delete',
              icon: <Trash2 size={15} />,
              danger: true,
              onSelect: () => void actions.deleteDiagram(diagram),
            },
          ]}
        />
      </div>
    </div>
  )
}

export default memo(DiagramRow)
