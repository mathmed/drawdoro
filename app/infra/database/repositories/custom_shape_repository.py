import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.custom_shape_repository import CustomShapeRepository
from app.domain.entities.models.custom_shape import CustomShape
from app.infra.database.models.custom_shape import CustomShapeORM


class CustomShapeRepositoryImpl(CustomShapeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, shape: CustomShape) -> CustomShape:
        orm = CustomShapeORM(
            id=shape.id,
            workspace_id=shape.workspace_id,
            name=shape.name,
            shape_definition=shape.shape_definition,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, shape_id: uuid.UUID) -> CustomShape | None:
        result = await self._session.execute(
            select(CustomShapeORM).where(CustomShapeORM.id == shape_id)
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[CustomShape]:
        result = await self._session.execute(
            select(CustomShapeORM).where(CustomShapeORM.workspace_id == workspace_id)
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def delete(self, shape_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(CustomShapeORM).where(CustomShapeORM.id == shape_id)
        )
        orm = result.scalar_one()
        await self._session.delete(orm)
        await self._session.commit()


def _to_domain(orm: CustomShapeORM) -> CustomShape:
    return CustomShape(
        id=orm.id,
        workspace_id=orm.workspace_id,
        name=orm.name,
        shape_definition=orm.shape_definition,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
