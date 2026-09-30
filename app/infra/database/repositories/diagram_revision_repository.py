import uuid
from datetime import datetime

from sqlalchemy import ColumnElement, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.enums.revision_kind import RevisionKind
from app.domain.enums.revision_origin import RevisionOrigin
from app.infra.database.models.diagram_revision import DiagramRevisionORM

NEWEST_FIRST = (DiagramRevisionORM.updated_at.desc(), DiagramRevisionORM.id.desc())


class DiagramRevisionRepositoryImpl(DiagramRevisionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, revision: DiagramRevision) -> DiagramRevision:
        snapshot = revision.snapshot or DiagramSnapshot(name="")
        orm = DiagramRevisionORM(
            id=revision.id,
            diagram_id=revision.diagram_id,
            kind=revision.kind.value,
            origin=revision.origin.value,
            author_id=revision.author_id,
            author_name=revision.author_name,
            author_picture_url=revision.author_picture_url,
            agent_name=revision.agent_name,
            agent_label=revision.agent_label,
            summary=revision.summary,
            restored_from_id=revision.restored_from_id,
            name=snapshot.name,
            canvas_state=snapshot.canvas_state,
            semantic_metadata=snapshot.semantic_metadata,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
        )
        self._session.add(orm)
        await self._session.commit()
        return await self._require(revision.diagram_id, revision.id)

    async def update_snapshot(self, revision: DiagramRevision) -> DiagramRevision:
        result = await self._session.execute(
            select(DiagramRevisionORM).where(DiagramRevisionORM.id == revision.id)
        )
        orm = result.scalar_one()
        snapshot = revision.snapshot or DiagramSnapshot(name=orm.name)
        orm.name = snapshot.name
        orm.canvas_state = snapshot.canvas_state
        orm.semantic_metadata = snapshot.semantic_metadata
        orm.updated_at = revision.updated_at
        await self._session.commit()
        return await self._require(revision.diagram_id, revision.id)

    async def get(self, diagram_id: uuid.UUID, revision_id: uuid.UUID) -> DiagramRevision | None:
        result = await self._session.execute(
            select(DiagramRevisionORM).where(
                DiagramRevisionORM.diagram_id == diagram_id,
                DiagramRevisionORM.id == revision_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm, with_snapshot=True) if orm else None

    async def get_latest(self, diagram_id: uuid.UUID) -> DiagramRevision | None:
        result = await self._session.execute(
            select(DiagramRevisionORM)
            .where(DiagramRevisionORM.diagram_id == diagram_id)
            .order_by(*NEWEST_FIRST)
            .limit(1)
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm, with_snapshot=True) if orm else None

    async def list_by_diagram(self, diagram_id: uuid.UUID, limit: int) -> list[DiagramRevision]:
        result = await self._session.execute(
            select(DiagramRevisionORM)
            .options(
                defer(DiagramRevisionORM.canvas_state),
                defer(DiagramRevisionORM.semantic_metadata),
            )
            .where(DiagramRevisionORM.diagram_id == diagram_id)
            .order_by(*NEWEST_FIRST)
            .limit(limit)
        )
        return [_to_domain(orm, with_snapshot=False) for orm in result.scalars().all()]

    async def prune(
        self, diagram_id: uuid.UUID, keep_latest: int | None, older_than: datetime | None
    ) -> None:
        ranked = (
            select(
                DiagramRevisionORM.id,
                DiagramRevisionORM.updated_at,
                func.row_number().over(order_by=NEWEST_FIRST).label("position"),
            )
            .where(DiagramRevisionORM.diagram_id == diagram_id)
            .subquery()
        )
        rules: list[ColumnElement[bool]] = []
        if keep_latest is not None:
            rules.append(ranked.c.position > keep_latest)
        if older_than is not None:
            rules.append(and_(ranked.c.updated_at < older_than, ranked.c.position > 1))
        if not rules:
            return
        expired = select(ranked.c.id).where(or_(*rules))
        await self._session.execute(
            delete(DiagramRevisionORM).where(DiagramRevisionORM.id.in_(expired))
        )
        await self._session.commit()

    async def _require(self, diagram_id: uuid.UUID, revision_id: uuid.UUID) -> DiagramRevision:
        revision = await self.get(diagram_id, revision_id)
        if revision is None:
            raise LookupError(f"Revision {revision_id} vanished while being saved")
        return revision


def _to_domain(orm: DiagramRevisionORM, *, with_snapshot: bool) -> DiagramRevision:
    snapshot = (
        DiagramSnapshot(
            name=orm.name,
            canvas_state=orm.canvas_state,
            semantic_metadata=orm.semantic_metadata,
        )
        if with_snapshot
        else None
    )
    return DiagramRevision(
        id=orm.id,
        diagram_id=orm.diagram_id,
        kind=RevisionKind(orm.kind),
        origin=RevisionOrigin(orm.origin),
        author_id=orm.author_id,
        author_name=orm.author_name,
        author_picture_url=orm.author_picture_url,
        agent_name=orm.agent_name,
        agent_label=orm.agent_label,
        summary=orm.summary,
        restored_from_id=orm.restored_from_id,
        snapshot=snapshot,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
