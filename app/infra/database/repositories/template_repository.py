import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.template_repository import TemplateRepository
from app.domain.entities.models.template import Template
from app.infra.database.models.template import TemplateORM


class TemplateRepositoryImpl(TemplateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, template: Template) -> Template:
        orm = TemplateORM(
            id=template.id,
            workspace_id=template.workspace_id,
            name=template.name,
            description=template.description,
            canvas_state=template.canvas_state,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, template_id: uuid.UUID) -> Template | None:
        result = await self._session.execute(
            select(TemplateORM).where(TemplateORM.id == template_id)
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_all(self, workspace_id: uuid.UUID | None = None) -> list[Template]:
        stmt = select(TemplateORM)
        if workspace_id is not None:
            stmt = stmt.where(TemplateORM.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars().all()]

    async def delete(self, template_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(TemplateORM).where(TemplateORM.id == template_id)
        )
        orm = result.scalar_one()
        await self._session.delete(orm)
        await self._session.commit()


def _to_domain(orm: TemplateORM) -> Template:
    return Template(
        id=orm.id,
        workspace_id=orm.workspace_id,
        name=orm.name,
        description=orm.description,
        canvas_state=orm.canvas_state,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
