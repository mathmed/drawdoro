import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.entities.models.folder import Folder
from app.infra.database.models.folder import FolderORM


class FolderRepositoryImpl(FolderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, folder: Folder) -> Folder:
        orm = FolderORM(
            id=folder.id,
            project_id=folder.project_id,
            parent_folder_id=folder.parent_folder_id,
            name=folder.name,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, folder_id: uuid.UUID) -> Folder | None:
        result = await self._session.execute(
            select(FolderORM).where(
                FolderORM.id == folder_id,
                FolderORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_by_project(self, project_id: uuid.UUID) -> list[Folder]:
        result = await self._session.execute(
            select(FolderORM).where(
                FolderORM.project_id == project_id,
                FolderORM.deleted_at.is_(None),
            )
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def update(self, folder: Folder) -> Folder:
        result = await self._session.execute(
            select(FolderORM).where(
                FolderORM.id == folder.id,
                FolderORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.name = folder.name
        orm.parent_folder_id = folder.parent_folder_id
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def delete(self, folder_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(FolderORM).where(
                FolderORM.id == folder_id,
                FolderORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.deleted_at = datetime.now(UTC)
        await self._session.commit()


def _to_domain(orm: FolderORM) -> Folder:
    return Folder(
        id=orm.id,
        project_id=orm.project_id,
        parent_folder_id=orm.parent_folder_id,
        name=orm.name,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )
