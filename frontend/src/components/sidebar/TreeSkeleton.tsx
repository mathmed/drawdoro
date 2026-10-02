import { Skeleton, SkeletonGroup } from '../ui/loading/Skeleton'
import { INDENT } from './RowMenu'

const TREE_WIDTHS = [72, 56, 64]
const PROJECT_WIDTHS = [64, 48, 56]

// Shown when a project with no cached tree is expanded, until its tree arrives.
export default function TreeSkeleton() {
  return (
    <SkeletonGroup label="Loading diagrams">
      {TREE_WIDTHS.map((width) => (
        <div key={width} className="tree-row tree-skeleton" style={{ paddingLeft: 8 + INDENT + 18 }}>
          <Skeleton className="skeleton-icon" />
          <Skeleton className="skeleton-line" width={`${width}%`} />
        </div>
      ))}
    </SkeletonGroup>
  )
}

// Project rows (chevron, icon, name) while a workspace's projects load.
export function ProjectListSkeleton() {
  return (
    <SkeletonGroup label="Loading projects" className="project-list-skeleton">
      {PROJECT_WIDTHS.map((width) => (
        <div key={width} className="tree-row" style={{ paddingLeft: 8 }}>
          <Skeleton width={14} height={14} radius={4} />
          <Skeleton className="skeleton-icon" />
          <Skeleton className="skeleton-line" width={`${width}%`} />
        </div>
      ))}
    </SkeletonGroup>
  )
}
