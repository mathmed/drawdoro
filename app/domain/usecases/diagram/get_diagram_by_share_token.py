from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError


class GetDiagramByShareTokenParams(InputData):
    share_token: str


class GetDiagramByShareToken(Usecase[GetDiagramByShareTokenParams, Diagram]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetDiagramByShareTokenParams) -> Diagram:
        diagram = await self._repo.get_by_share_token(params.share_token)
        if diagram is None:
            raise NotFoundError("Shared diagram not found")
        return diagram
