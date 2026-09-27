from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.workspace.create_workspace import CreateWorkspace
from app.domain.usecases.workspace.delete_workspace import DeleteWorkspace
from app.domain.usecases.workspace.get_workspace import GetWorkspace
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces
from app.domain.usecases.workspace.update_workspace import UpdateWorkspace
from app.infra.database.repositories.workspace_repository import WorkspaceRepositoryImpl
from app.infra.database.session import get_session


async def create_workspace_factory(session: AsyncSession = Depends(get_session)) -> CreateWorkspace:
    return CreateWorkspace(WorkspaceRepositoryImpl(session))


async def get_workspace_factory(session: AsyncSession = Depends(get_session)) -> GetWorkspace:
    return GetWorkspace(WorkspaceRepositoryImpl(session))


async def list_workspaces_factory(session: AsyncSession = Depends(get_session)) -> ListWorkspaces:
    return ListWorkspaces(WorkspaceRepositoryImpl(session))


async def update_workspace_factory(session: AsyncSession = Depends(get_session)) -> UpdateWorkspace:
    return UpdateWorkspace(WorkspaceRepositoryImpl(session))


async def delete_workspace_factory(session: AsyncSession = Depends(get_session)) -> DeleteWorkspace:
    return DeleteWorkspace(WorkspaceRepositoryImpl(session))
