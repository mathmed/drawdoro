import { INDENT } from './RowMenu'

const WIDTHS = [72, 56, 64]

// Shown the moment a project with no cached tree is expanded, until its tree arrives.
export default function TreeSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading diagrams">
      {WIDTHS.map((width) => (
        <div key={width} className="tree-row tree-skeleton" style={{ paddingLeft: 8 + INDENT + 18 }}>
          <span className="skeleton skeleton-icon" />
          <span className="skeleton skeleton-line" style={{ width: `${width}%` }} />
        </div>
      ))}
    </div>
  )
}
