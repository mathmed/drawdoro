import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
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
            mermaid_source=diagram.mermaid_source,
            d2_source=diagram.d2_source,
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

    async def list_by_project(self, project_id: uuid.UUID) -> list[Diagram]:
        result = await self._session.execute(
            select(DiagramORM).where(
                DiagramORM.project_id == project_id,
                DiagramORM.deleted_at.is_(None),
            )
        )
        return [_to_domain(row) for row in result.scalars().all()]

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
        orm.mermaid_source = diagram.mermaid_source
        orm.d2_source = diagram.d2_source
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
        mermaid_source=orm.mermaid_source,
        d2_source=orm.d2_source,
        semantic_metadata=orm.semantic_metadata,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )
