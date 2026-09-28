from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.workspace_member.add_workspace_member import AddWorkspaceMember
from app.domain.usecases.workspace_member.list_workspace_members import ListWorkspaceMembers
from app.domain.usecases.workspace_member.remove_workspace_member import RemoveWorkspaceMember
from app.domain.usecases.workspace_member.update_workspace_member_role import (
    UpdateWorkspaceMemberRole,
)
from app.infra.database.repositories.user_repository import UserRepositoryImpl
from app.infra.database.repositories.workspace_member_repository import (
    WorkspaceMemberRepositoryImpl,
)
from app.infra.database.session import get_session


async def list_workspace_members_factory(
    session: AsyncSession = Depends(get_session),
) -> ListWorkspaceMembers:
    return ListWorkspaceMembers(WorkspaceMemberRepositoryImpl(session))


async def add_workspace_member_factory(
    session: AsyncSession = Depends(get_session),
) -> AddWorkspaceMember:
    return AddWorkspaceMember(WorkspaceMemberRepositoryImpl(session), UserRepositoryImpl(session))


async def update_workspace_member_role_factory(
    session: AsyncSession = Depends(get_session),
) -> UpdateWorkspaceMemberRole:
    return UpdateWorkspaceMemberRole(WorkspaceMemberRepositoryImpl(session))


async def remove_workspace_member_factory(
    session: AsyncSession = Depends(get_session),
) -> RemoveWorkspaceMember:
    return RemoveWorkspaceMember(WorkspaceMemberRepositoryImpl(session))
