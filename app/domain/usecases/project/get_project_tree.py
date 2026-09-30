import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.project_tree import ProjectTree


class GetProjectTreeParams(InputData):
    project_id: uuid.UUID


class GetProjectTree(Usecase[GetProjectTreeParams, ProjectTree]):
    def __init__(self, folders: FolderRepository, diagrams: DiagramRepository) -> None:
        self._folders = folders
        self._diagrams = diagrams

    async def execute(self, params: GetProjectTreeParams) -> ProjectTree:
        folders = await self._folders.list_by_project(params.project_id)
        diagrams = await self._diagrams.list_by_project(params.project_id)
        return ProjectTree(folders=folders, diagrams=diagrams)
