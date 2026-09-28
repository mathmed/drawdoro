import { BookOpenText, MessageSquare, Tags, X } from 'lucide-react'

import { useAppStore, type InspectorTab } from '../../store/useAppStore'
import CommentsPanel from '../comments/CommentsPanel'
import DocsPanel from '../docs/DocsPanel'
import SemanticPanel from '../semantic/SemanticPanel'

const TABS: { id: InspectorTab; label: string; icon: typeof Tags }[] = [
  { id: 'properties', label: 'Properties', icon: Tags },
  { id: 'docs', label: 'Docs', icon: BookOpenText },
  { id: 'comments', label: 'Comments', icon: MessageSquare },
]

export default function Inspector() {
  const inspectorTab = useAppStore((state) => state.inspectorTab)
  const openInspector = useAppStore((state) => state.openInspector)
  const closeInspector = useAppStore((state) => state.closeInspector)
  const commentCount = useAppStore((state) => state.comments.length)

  const counts: Partial<Record<InspectorTab, number>> = { comments: commentCount }

  return (
    <aside className="inspector">
      <div className="inspector-header">
        <div className="inspector-tabs" role="tablist">
          {TABS.map(({ id, label, icon: Icon }) => {
            const count = counts[id] ?? 0
            return (
              <button
                key={id}
                type="button"
                role="tab"
                className="inspector-tab"
                aria-selected={inspectorTab === id}
                onClick={() => openInspector(id)}
              >
                <Icon size={14} />
                {label}
                {count > 0 ? <span className="count">{count}</span> : null}
              </button>
            )
          })}
        </div>
        <button type="button" className="btn btn-ghost btn-icon btn-sm" aria-label="Close panel" onClick={closeInspector}>
          <X size={16} />
        </button>
      </div>
      <div className="inspector-body">
        {inspectorTab === 'properties' ? <SemanticPanel /> : null}
        {inspectorTab === 'docs' ? <DocsPanel /> : null}
        {inspectorTab === 'comments' ? <CommentsPanel /> : null}
      </div>
    </aside>
  )
}
