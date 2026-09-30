import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.entities.models.api_key import ApiKey
from app.infra.database.models.api_key import ApiKeyORM


class ApiKeyRepositoryImpl(ApiKeyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, api_key: ApiKey) -> ApiKey:
        orm = ApiKeyORM(
            id=api_key.id,
            user_id=api_key.user_id,
            label=api_key.label,
            prefix=api_key.prefix,
            key_hash=api_key.key_hash,
            created_at=api_key.created_at,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def list_active_by_user(self, user_id: uuid.UUID) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKeyORM)
            .where(ApiKeyORM.user_id == user_id, ApiKeyORM.revoked_at.is_(None))
            .order_by(ApiKeyORM.created_at.desc())
        )
        return [_to_domain(orm) for orm in result.scalars().all()]

    async def get_active_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyORM).where(ApiKeyORM.key_hash == key_hash, ApiKeyORM.revoked_at.is_(None))
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def get_active(self, key_id: uuid.UUID, user_id: uuid.UUID) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyORM).where(
                ApiKeyORM.id == key_id,
                ApiKeyORM.user_id == user_id,
                ApiKeyORM.revoked_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def revoke(self, key_id: uuid.UUID, revoked_at: datetime) -> None:
        await self._session.execute(
            update(ApiKeyORM).where(ApiKeyORM.id == key_id).values(revoked_at=revoked_at)
        )
        await self._session.commit()

    async def mark_used(self, key_id: uuid.UUID, used_at: datetime) -> None:
        await self._session.execute(
            update(ApiKeyORM).where(ApiKeyORM.id == key_id).values(last_used_at=used_at)
        )
        await self._session.commit()


def _to_domain(orm: ApiKeyORM) -> ApiKey:
    return ApiKey(
        id=orm.id,
        user_id=orm.user_id,
        label=orm.label,
        prefix=orm.prefix,
        key_hash=orm.key_hash,
        created_at=orm.created_at,
        last_used_at=orm.last_used_at,
        revoked_at=orm.revoked_at,
    )
