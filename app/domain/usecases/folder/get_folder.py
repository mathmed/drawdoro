import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.folder import Folder
from app.domain.errors.domain_errors import NotFoundError


class GetFolderParams(InputData):
    folder_id: uuid.UUID


class GetFolder(Usecase[GetFolderParams, Folder]):
    def __init__(self, repo: FolderRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetFolderParams) -> Folder:
        folder = await self._repo.get_by_id(params.folder_id)
        if folder is None:
            raise NotFoundError(f"Folder {params.folder_id} not found")
        return folder
