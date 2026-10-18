import uuid

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.errors.domain_errors import NotFoundError


# Folders and diagrams live in a project and, optionally, in a folder of that same project. Deleted
# projects and folders don't count, and a folder of another project is reported as not found, like
# workspace access does, so its existence doesn't leak.
class ProjectPlacement:
    def __init__(self, projects: ProjectRepository, folders: FolderRepository) -> None:
        self._projects = projects
        self._folders = folders

    async def check_new(self, project_id: uuid.UUID, folder_id: uuid.UUID | None) -> None:
        if await self._projects.get_by_id(project_id) is None:
            raise NotFoundError(f"Project {project_id} not found")
        await self._check_folder(project_id, folder_id)

    # Only a different folder is checked: editors send back the folder an item is in, which may
    # have been deleted since (deleting a folder leaves its contents where they are).
    async def check_move(
        self,
        project_id: uuid.UUID,
        current_folder_id: uuid.UUID | None,
        folder_id: uuid.UUID | None,
    ) -> None:
        if folder_id == current_folder_id:
            return
        await self._check_folder(project_id, folder_id)

    async def _check_folder(self, project_id: uuid.UUID, folder_id: uuid.UUID | None) -> None:
        if folder_id is None:
            return
        folder = await self._folders.get_by_id(folder_id)
        if folder is None or folder.project_id != project_id:
            raise NotFoundError(f"Folder {folder_id} not found")
