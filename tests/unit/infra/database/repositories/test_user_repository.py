import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities.models.user import User
from app.infra.database.models.documentation_page import DocumentationPageORM
from app.infra.database.models.user import UserORM
from app.infra.database.repositories.user_repository import UserRepositoryImpl

NOW = datetime(2026, 10, 1, 12, tzinfo=UTC)


def stamp(orm: UserORM | DocumentationPageORM) -> None:
    orm.created_at = orm.created_at or NOW
    orm.updated_at = orm.updated_at or NOW


def found(orm: UserORM | DocumentationPageORM | None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = orm
    result.scalar_one.return_value = orm
    return result


def user_orm(**values: object) -> UserORM:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "email": "ada@example.com",
        "name": "Ada",
        "picture_url": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    return UserORM(**(defaults | values))


def page_orm(**values: object) -> DocumentationPageORM:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "diagram_id": uuid.uuid4(),
        "content": "# Old",
        "created_at": NOW,
        "updated_at": NOW,
    }
    return DocumentationPageORM(**(defaults | values))


@pytest.fixture
def session() -> AsyncMock:
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.refresh.side_effect = stamp
    return mock


@pytest.fixture
def sut(session: AsyncMock) -> UserRepositoryImpl:
    return UserRepositoryImpl(session)


async def test_should_map_the_user_found_by_id(sut: UserRepositoryImpl, session: AsyncMock) -> None:
    orm = user_orm()
    session.execute.return_value = found(orm)
    user = await sut.get_by_id(orm.id)
    assert user == User(
        id=orm.id, email="ada@example.com", name="Ada", created_at=NOW, updated_at=NOW
    )


async def test_should_return_none_when_no_user_has_the_id(
    sut: UserRepositoryImpl, session: AsyncMock
) -> None:
    session.execute.return_value = found(None)
    assert await sut.get_by_id(uuid.uuid4()) is None


async def test_should_find_the_user_by_email(sut: UserRepositoryImpl, session: AsyncMock) -> None:
    orm = user_orm(email="grace@example.com")
    session.execute.return_value = found(orm)
    user = await sut.get_by_email("grace@example.com")
    assert user is not None
    assert user.id == orm.id
    session.execute.return_value = found(None)
    assert await sut.get_by_email("nobody@example.com") is None


async def test_should_create_the_user_and_commit(
    sut: UserRepositoryImpl, session: AsyncMock
) -> None:
    user = User(email="ada@example.com", name="Ada", picture_url="https://pic")
    created = await sut.create(user)
    added = session.add.call_args.args[0]
    assert (added.id, added.email, added.name, added.picture_url) == (
        user.id,
        "ada@example.com",
        "Ada",
        "https://pic",
    )
    session.commit.assert_awaited_once()
    assert created.id == user.id


async def test_should_update_only_the_name_and_picture(
    sut: UserRepositoryImpl, session: AsyncMock
) -> None:
    orm = user_orm()
    session.execute.return_value = found(orm)
    changed = User(id=orm.id, email="other@example.com", name="Ada L.", picture_url="https://new")
    updated = await sut.update(changed)
    assert (orm.name, orm.picture_url, orm.email) == ("Ada L.", "https://new", "ada@example.com")
    session.commit.assert_awaited_once()
    assert updated.name == "Ada L."
