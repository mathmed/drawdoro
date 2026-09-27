import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import NotFoundError


class DeleteFolderParams(InputData):
    folder_id: uuid.UUID


class DeleteFolder(Usecase[DeleteFolderParams, None]):
    def __init__(self, repo: FolderRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteFolderParams) -> None:
        folder = await self._repo.get_by_id(params.folder_id)
        if folder is None:
            raise NotFoundError(f"Folder {params.folder_id} not found")
        await self._repo.delete(params.folder_id)
