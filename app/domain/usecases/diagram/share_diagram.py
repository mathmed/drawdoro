import secrets
import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError

SHARE_TOKEN_BYTES = 9


class ShareDiagramParams(InputData):
    diagram_id: uuid.UUID


class ShareDiagram(Usecase[ShareDiagramParams, Diagram]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: ShareDiagramParams) -> Diagram:
        diagram = await self._repo.get_by_id(params.diagram_id)
        if diagram is None:
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        # A diagram keeps the same shareable link once generated, so repeated calls are idempotent.
        if diagram.share_token is not None:
            return diagram
        token = secrets.token_urlsafe(SHARE_TOKEN_BYTES)
        return await self._repo.set_share_token(diagram.id, token)
