from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.project.create_project import CreateProject
from app.domain.usecases.project.delete_project import DeleteProject
from app.domain.usecases.project.get_project import GetProject
from app.domain.usecases.project.get_project_tree import GetProjectTree
from app.domain.usecases.project.list_projects import ListProjects
from app.domain.usecases.project.update_project import UpdateProject
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.repositories.folder_repository import FolderRepositoryImpl
from app.infra.database.repositories.project_repository import ProjectRepositoryImpl
from app.infra.database.session import get_session


async def create_project_factory(session: AsyncSession = Depends(get_session)) -> CreateProject:
    return CreateProject(ProjectRepositoryImpl(session))


async def get_project_factory(session: AsyncSession = Depends(get_session)) -> GetProject:
    return GetProject(ProjectRepositoryImpl(session))


async def list_projects_factory(session: AsyncSession = Depends(get_session)) -> ListProjects:
    return ListProjects(ProjectRepositoryImpl(session))


async def update_project_factory(session: AsyncSession = Depends(get_session)) -> UpdateProject:
    return UpdateProject(ProjectRepositoryImpl(session))


async def delete_project_factory(session: AsyncSession = Depends(get_session)) -> DeleteProject:
    return DeleteProject(ProjectRepositoryImpl(session))


async def get_project_tree_factory(session: AsyncSession = Depends(get_session)) -> GetProjectTree:
    return GetProjectTree(FolderRepositoryImpl(session), DiagramRepositoryImpl(session))
