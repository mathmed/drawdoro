import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.folder import Folder


class CreateFolderParams(InputData):
    project_id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None = None


class CreateFolder(Usecase[CreateFolderParams, Folder]):
    def __init__(self, repo: FolderRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateFolderParams) -> Folder:
        folder = Folder(
            project_id=params.project_id, name=params.name, parent_folder_id=params.parent_folder_id
        )
        return await self._repo.create(folder)
