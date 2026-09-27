import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.folder import Folder
from app.domain.errors.domain_errors import NotFoundError


class UpdateFolderParams(InputData):
    folder_id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None = None


class UpdateFolder(Usecase[UpdateFolderParams, Folder]):
    def __init__(self, repo: FolderRepository) -> None:
        self._repo = repo

    async def execute(self, params: UpdateFolderParams) -> Folder:
        folder = await self._repo.get_by_id(params.folder_id)
        if folder is None:
            raise NotFoundError(f"Folder {params.folder_id} not found")
        folder.name = params.name
        folder.parent_folder_id = params.parent_folder_id
        return await self._repo.update(folder)
