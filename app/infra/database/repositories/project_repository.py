import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.infra.database.models.project import ProjectORM


class ProjectRepositoryImpl(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, project: Project) -> Project:
        orm = ProjectORM(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self._session.execute(
            select(ProjectORM).where(
                ProjectORM.id == project_id,
                ProjectORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Project]:
        result = await self._session.execute(
            select(ProjectORM).where(
                ProjectORM.workspace_id == workspace_id,
                ProjectORM.deleted_at.is_(None),
            )
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def update(self, project: Project) -> Project:
        result = await self._session.execute(
            select(ProjectORM).where(
                ProjectORM.id == project.id,
                ProjectORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.name = project.name
        orm.description = project.description
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def delete(self, project_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(ProjectORM).where(
                ProjectORM.id == project_id,
                ProjectORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.deleted_at = datetime.now(UTC)
        await self._session.commit()


def _to_domain(orm: ProjectORM) -> Project:
    return Project(
        id=orm.id,
        workspace_id=orm.workspace_id,
        name=orm.name,
        description=orm.description,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )
