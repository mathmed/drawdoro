import uuid
from datetime import UTC, datetime

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import ConflictError
from app.infra.database.models.workspace import WorkspaceORM
from app.infra.database.models.workspace_member import WorkspaceMemberORM

# Postgres' name for the UNIQUE (slug) of the initial migration. It covers deleted workspaces too.
SLUG_CONSTRAINT = "workspaces_slug_key"


class WorkspaceRepositoryImpl(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workspace: Workspace) -> Workspace:
        orm = WorkspaceORM(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
        )
        self._session.add(orm)
        await self._commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        result = await self._session.execute(
            select(WorkspaceORM).where(
                WorkspaceORM.id == workspace_id,
                WorkspaceORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_all(self) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceORM).where(WorkspaceORM.deleted_at.is_(None))
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def list_for_user(self, user_id: uuid.UUID) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceORM)
            .join(WorkspaceMemberORM, WorkspaceMemberORM.workspace_id == WorkspaceORM.id)
            .where(WorkspaceMemberORM.user_id == user_id, WorkspaceORM.deleted_at.is_(None))
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def list_without_members(self) -> list[Workspace]:
        has_members = select(WorkspaceMemberORM.id).where(
            WorkspaceMemberORM.workspace_id == WorkspaceORM.id
        )
        result = await self._session.execute(
            select(WorkspaceORM).where(WorkspaceORM.deleted_at.is_(None), ~has_members.exists())
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def update(self, workspace: Workspace) -> Workspace:
        result = await self._session.execute(
            select(WorkspaceORM).where(
                WorkspaceORM.id == workspace.id,
                WorkspaceORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.name = workspace.name
        orm.slug = workspace.slug
        await self._commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def delete(self, workspace_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(WorkspaceORM).where(
                WorkspaceORM.id == workspace_id,
                WorkspaceORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.deleted_at = datetime.now(UTC)
        await self._session.commit()

    # The unique constraint is what decides, so two requests racing for a free slug get a 201 and
    # a 409 rather than a 500.
    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if _is_slug_taken(error):
                raise ConflictError("Another workspace already uses this slug") from error
            raise


def _is_slug_taken(error: IntegrityError) -> bool:
    cause = error.driver_exception
    return isinstance(cause, UniqueViolationError) and cause.constraint_name == SLUG_CONSTRAINT


def _to_domain(orm: WorkspaceORM) -> Workspace:
    return Workspace(
        id=orm.id,
        name=orm.name,
        slug=orm.slug,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )
