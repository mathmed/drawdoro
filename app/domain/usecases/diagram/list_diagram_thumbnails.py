import uuid

from app.domain.contracts.diagram_thumbnail_repository import DiagramThumbnailRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.thumbnail_theme import ThumbnailTheme


class ListDiagramThumbnailsParams(InputData):
    project_id: uuid.UUID
    theme: ThumbnailTheme = ThumbnailTheme.LIGHT


class ListDiagramThumbnails(Usecase[ListDiagramThumbnailsParams, list[DiagramThumbnail]]):
    def __init__(self, repo: DiagramThumbnailRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListDiagramThumbnailsParams) -> list[DiagramThumbnail]:
        return await self._repo.list_by_project(params.project_id, params.theme)
