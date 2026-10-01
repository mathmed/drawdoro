import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_summary import DiagramSummary
from app.infra.database.models.diagram import DiagramORM


class DiagramRepositoryImpl(DiagramRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, diagram: Diagram) -> Diagram:
        orm = DiagramORM(
            id=diagram.id,
            project_id=diagram.project_id,
            folder_id=diagram.folder_id,
            name=diagram.name,
            canvas_state=diagram.canvas_state,
            semantic_metadata=diagram.semantic_metadata,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, diagram_id: uuid.UUID) -> Diagram | None:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.id == diagram_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def exists(self, diagram_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(DiagramORM.id).where(
                DiagramORM.id == diagram_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_by_share_token(self, share_token: str) -> Diagram | None:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.share_token == share_token,
                DiagramORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def set_share_token(self, diagram_id: uuid.UUID, share_token: str) -> Diagram:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.id == diagram_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.share_token = share_token
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def list_by_project(self, project_id: uuid.UUID) -> list[DiagramSummary]:
        # Only the metadata columns: loading every canvas snapshot made listings megabytes long.
        result = await self._session.execute(
            select(
                DiagramORM.id,
                DiagramORM.project_id,
                DiagramORM.folder_id,
                DiagramORM.name,
                DiagramORM.created_at,
                DiagramORM.updated_at,
            ).where(
                DiagramORM.project_id == project_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        return [DiagramSummary.model_validate(row._asdict()) for row in result.all()]

    async def list_by_folder(self, folder_id: uuid.UUID) -> list[Diagram]:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.folder_id == folder_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def update(self, diagram: Diagram) -> Diagram:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.id == diagram.id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.name = diagram.name
        orm.folder_id = diagram.folder_id
        orm.canvas_state = diagram.canvas_state
        orm.semantic_metadata = diagram.semantic_metadata
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def delete(self, diagram_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.id == diagram_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one()
        orm.deleted_at = datetime.now(UTC)
        await self._session.commit()


def _to_domain(orm: DiagramORM) -> Diagram:
    return Diagram(
        id=orm.id,
        project_id=orm.project_id,
        folder_id=orm.folder_id,
        name=orm.name,
        canvas_state=orm.canvas_state,
        semantic_metadata=orm.semantic_metadata,
        share_token=orm.share_token,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )
