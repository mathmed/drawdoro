import { Workflow } from 'lucide-react'

import { useThemeStore } from '../../store/useThemeStore'
import { projectKey, useThumbnailStore } from '../../store/useThumbnailStore'

interface DiagramCardPreviewProps {
  projectId: string
  diagramId: string
}

// The diagram's stored preview in the current theme; the placeholder icon when it has none, and an
// empty preview area while the project's previews are still loading, so the icon never flashes.
export default function DiagramCardPreview({ projectId, diagramId }: DiagramCardPreviewProps) {
  const theme = useThemeStore((state) => state.resolved)
  const project = useThumbnailStore((state) => state.byProject[projectKey(theme, projectId)])
  const src = project?.items[diagramId]?.src ?? null

  if (src !== null) {
    return (
      <div className="diagram-card-preview diagram-card-preview-image">
        <img src={src} alt="" draggable={false} decoding="async" />
      </div>
    )
  }
  return (
    <div className="diagram-card-preview" data-testid="diagram-card-placeholder">
      {project?.loaded === true ? <Workflow size={30} strokeWidth={1.5} /> : null}
    </div>
  )
}
