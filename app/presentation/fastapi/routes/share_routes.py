import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.diagram.get_diagram_by_share_token import (
    GetDiagramByShareToken,
    GetDiagramByShareTokenParams,
)
from app.domain.usecases.diagram.share_diagram import ShareDiagram, ShareDiagramParams
from app.presentation.factories.diagram_factories import (
    get_diagram_by_share_token_factory,
    share_diagram_factory,
)
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.diagram_schemas import (
    SharedDiagramResponse,
    ShareDiagramResponse,
)

# Generating the link needs an editor session, so it stays behind workspace access.
router = APIRouter(
    prefix="/diagrams/{diagram_id}/share",
    tags=["share"],
    dependencies=[Depends(require_workspace_access)],
)


@router.post("", response_model=ShareDiagramResponse, status_code=201)
async def share_diagram(
    diagram_id: uuid.UUID,
    use_case: ShareDiagram = Depends(share_diagram_factory),
) -> ShareDiagramResponse:
    diagram = await use_case.execute(ShareDiagramParams(diagram_id=diagram_id))
    return ShareDiagramResponse.model_validate(diagram)


# Public: anyone with the token can open the diagram, no sign-in required.
public_router = APIRouter(prefix="/share", tags=["share"])


@public_router.get("/{share_token}", response_model=SharedDiagramResponse)
async def get_shared_diagram(
    share_token: str,
    use_case: GetDiagramByShareToken = Depends(get_diagram_by_share_token_factory),
) -> SharedDiagramResponse:
    diagram = await use_case.execute(GetDiagramByShareTokenParams(share_token=share_token))
    return SharedDiagramResponse.model_validate(diagram)
