import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.entities.models.adr import Adr
from app.domain.enums.adr_status import AdrStatus
from app.infra.database.models.adr import AdrORM


class AdrRepositoryImpl(AdrRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, adr: Adr) -> Adr:
        orm = AdrORM(
            id=adr.id,
            diagram_id=adr.diagram_id,
            title=adr.title,
            context=adr.context,
            decision=adr.decision,
            consequences=adr.consequences,
            status=adr.status,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, adr_id: uuid.UUID) -> Adr | None:
        result = await self._session.execute(select(AdrORM).where(AdrORM.id == adr_id))
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_by_diagram(self, diagram_id: uuid.UUID) -> list[Adr]:
        result = await self._session.execute(select(AdrORM).where(AdrORM.diagram_id == diagram_id))
        return [_to_domain(row) for row in result.scalars().all()]

    async def update(self, adr: Adr) -> Adr:
        result = await self._session.execute(select(AdrORM).where(AdrORM.id == adr.id))
        orm = result.scalar_one()
        orm.title = adr.title
        orm.context = adr.context
        orm.decision = adr.decision
        orm.consequences = adr.consequences
        orm.status = adr.status
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def delete(self, adr_id: uuid.UUID) -> None:
        result = await self._session.execute(select(AdrORM).where(AdrORM.id == adr_id))
        orm = result.scalar_one()
        await self._session.delete(orm)
        await self._session.commit()


def _to_domain(orm: AdrORM) -> Adr:
    return Adr(
        id=orm.id,
        diagram_id=orm.diagram_id,
        title=orm.title,
        context=orm.context,
        decision=orm.decision,
        consequences=orm.consequences,
        status=AdrStatus(orm.status),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
