import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.user import User
from app.infra.database.models.user import UserORM


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(UserORM).where(UserORM.id == user_id))
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserORM).where(UserORM.email == email))
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def create(self, user: User) -> User:
        orm = UserORM(id=user.id, name=user.name, email=user.email, picture_url=user.picture_url)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def update(self, user: User) -> User:
        result = await self._session.execute(select(UserORM).where(UserORM.id == user.id))
        orm = result.scalar_one()
        orm.name = user.name
        orm.picture_url = user.picture_url
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)


def _to_domain(orm: UserORM) -> User:
    return User(
        id=orm.id,
        email=orm.email,
        name=orm.name,
        picture_url=orm.picture_url,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
