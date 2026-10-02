import { Skeleton, SkeletonGroup } from '../ui/loading/Skeleton'

const CARD_COUNT = 6
const NAME_WIDTHS = ['68%', '52%', '74%', '58%', '46%', '64%']

function DiagramCardSkeletons() {
  return (
    <div className="card-grid">
      {NAME_WIDTHS.slice(0, CARD_COUNT).map((width) => (
        <div key={width} className="diagram-card diagram-card-skeleton">
          <div className="diagram-card-preview">
            <Skeleton width={30} height={30} radius="var(--radius-md)" />
          </div>
          <div className="diagram-card-body">
            <Skeleton className="skeleton-line" width={width} height={13} />
            <Skeleton className="skeleton-line" width="38%" height={10} />
          </div>
        </div>
      ))}
    </div>
  )
}

// The diagram grid of a project whose tree is on its way.
export function DiagramGridSkeleton() {
  return (
    <SkeletonGroup label="Loading diagrams">
      <div className="home-section-title">
        <Skeleton className="skeleton-line" width={120} height={12} />
      </div>
      <DiagramCardSkeletons />
    </SkeletonGroup>
  )
}

// The whole overview (project header and diagram grid) while workspaces and projects load.
export default function HomeSkeleton() {
  return (
    <div className="home scroll">
      <SkeletonGroup label="Loading your workspace" className="home-inner">
        <div className="home-header">
          <div className="home-header-skeleton">
            <Skeleton className="skeleton-line" width={110} height={11} />
            <Skeleton width={260} height={26} />
            <Skeleton className="skeleton-line" width={180} height={12} />
          </div>
        </div>
        <div className="home-section-title">
          <Skeleton className="skeleton-line" width={120} height={12} />
        </div>
        <DiagramCardSkeletons />
      </SkeletonGroup>
    </div>
  )
}
