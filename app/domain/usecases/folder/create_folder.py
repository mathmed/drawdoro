import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.folder import Folder
from app.domain.services.project_placement import ProjectPlacement


class CreateFolderParams(InputData):
    project_id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None = None


class CreateFolder(Usecase[CreateFolderParams, Folder]):
    def __init__(self, repo: FolderRepository, placement: ProjectPlacement) -> None:
        self._repo = repo
        self._placement = placement

    async def execute(self, params: CreateFolderParams) -> Folder:
        await self._placement.check_new(params.project_id, params.parent_folder_id)
        folder = Folder(
            project_id=params.project_id, name=params.name, parent_folder_id=params.parent_folder_id
        )
        return await self._repo.create(folder)
