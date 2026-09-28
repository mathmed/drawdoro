import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails
from app.domain.enums.workspace_role import WorkspaceRole
from app.infra.database.models.user import UserORM
from app.infra.database.models.workspace_member import WorkspaceMemberORM


class WorkspaceMemberRepositoryImpl(WorkspaceMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> WorkspaceMember | None:
        result = await self._session.execute(
            select(WorkspaceMemberORM).where(
                WorkspaceMemberORM.workspace_id == workspace_id,
                WorkspaceMemberORM.user_id == user_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_details(self, workspace_id: uuid.UUID) -> list[WorkspaceMemberDetails]:
        result = await self._session.execute(
            select(WorkspaceMemberORM, UserORM)
            .join(UserORM, UserORM.id == WorkspaceMemberORM.user_id)
            .where(WorkspaceMemberORM.workspace_id == workspace_id)
            .order_by(UserORM.name)
        )
        return [
            WorkspaceMemberDetails(
                user_id=user.id, name=user.name, email=user.email, role=WorkspaceRole(member.role)
            )
            for member, user in result.all()
        ]

    async def create(self, member: WorkspaceMember) -> WorkspaceMember:
        orm = WorkspaceMemberORM(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role.value,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def update(self, member: WorkspaceMember) -> WorkspaceMember:
        result = await self._session.execute(
            select(WorkspaceMemberORM).where(WorkspaceMemberORM.id == member.id)
        )
        orm = result.scalar_one()
        orm.role = member.role.value
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def delete(self, member_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(WorkspaceMemberORM).where(WorkspaceMemberORM.id == member_id)
        )
        await self._session.commit()

    async def count_owners(self, workspace_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                WorkspaceMemberORM.workspace_id == workspace_id,
                WorkspaceMemberORM.role == WorkspaceRole.OWNER.value,
            )
        )
        return int(result.scalar_one())


def _to_domain(orm: WorkspaceMemberORM) -> WorkspaceMember:
    return WorkspaceMember(
        id=orm.id,
        workspace_id=orm.workspace_id,
        user_id=orm.user_id,
        role=WorkspaceRole(orm.role),
        created_at=orm.created_at,
    )
