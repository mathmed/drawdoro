import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.folder import Folder


class ListFoldersParams(InputData):
    project_id: uuid.UUID


class ListFolders(Usecase[ListFoldersParams, list[Folder]]):
    def __init__(self, repo: FolderRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListFoldersParams) -> list[Folder]:
        return await self._repo.list_by_project(params.project_id)
