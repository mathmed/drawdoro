import uuid

from fastapi import APIRouter, Depends, Query

from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.usecases.revision.get_diagram_revision import (
    GetDiagramRevision,
    GetDiagramRevisionParams,
)
from app.domain.usecases.revision.list_diagram_revisions import (
    MAX_LISTED_REVISIONS,
    ListDiagramRevisions,
    ListDiagramRevisionsParams,
)
from app.domain.usecases.revision.restore_diagram_revision import (
    RestoreDiagramRevision,
    RestoreDiagramRevisionParams,
)
from app.presentation.factories.revision_factories import (
    get_diagram_revision_factory,
    list_diagram_revisions_factory,
    restore_diagram_revision_factory,
)
from app.presentation.fastapi.dependencies.agent_presence import track_agent_activity
from app.presentation.fastapi.dependencies.revision_author import get_revision_author
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.diagram_schemas import DiagramResponse
from app.presentation.fastapi.schemas.revision_schemas import (
    RevisionDetailResponse,
    RevisionResponse,
)

# Reads need any membership; restoring is a write, so it needs the editor role.
router = APIRouter(
    prefix="/diagrams/{diagram_id}/revisions",
    tags=["revisions"],
    dependencies=[Depends(require_workspace_access), Depends(track_agent_activity)],
)


@router.get("", response_model=list[RevisionResponse])
async def list_revisions(
    diagram_id: uuid.UUID,
    limit: int = Query(default=MAX_LISTED_REVISIONS, ge=1, le=MAX_LISTED_REVISIONS),
    use_case: ListDiagramRevisions = Depends(list_diagram_revisions_factory),
) -> list[RevisionResponse]:
    revisions = await use_case.execute(
        ListDiagramRevisionsParams(diagram_id=diagram_id, limit=limit)
    )
    return [RevisionResponse.model_validate(revision) for revision in revisions]


@router.get("/{revision_id}", response_model=RevisionDetailResponse)
async def get_revision(
    diagram_id: uuid.UUID,
    revision_id: uuid.UUID,
    use_case: GetDiagramRevision = Depends(get_diagram_revision_factory),
) -> RevisionDetailResponse:
    revision = await use_case.execute(
        GetDiagramRevisionParams(diagram_id=diagram_id, revision_id=revision_id)
    )
    return RevisionDetailResponse.from_revision(revision)


@router.post("/{revision_id}/restore", response_model=DiagramResponse)
async def restore_revision(
    diagram_id: uuid.UUID,
    revision_id: uuid.UUID,
    author: RevisionAuthor = Depends(get_revision_author),
    use_case: RestoreDiagramRevision = Depends(restore_diagram_revision_factory),
) -> DiagramResponse:
    diagram = await use_case.execute(
        RestoreDiagramRevisionParams(diagram_id=diagram_id, revision_id=revision_id, author=author)
    )
    return DiagramResponse.model_validate(diagram)
