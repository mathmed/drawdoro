import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities.models.documentation_page import DocumentationPage
from app.infra.database.models.documentation_page import DocumentationPageORM
from app.infra.database.models.user import UserORM
from app.infra.database.repositories.documentation_page_repository import (
    DocumentationPageRepositoryImpl,
)

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
def sut(session: AsyncMock) -> DocumentationPageRepositoryImpl:
    return DocumentationPageRepositoryImpl(session)


async def test_should_map_the_page_of_the_diagram(
    sut: DocumentationPageRepositoryImpl, session: AsyncMock
) -> None:
    orm = page_orm()
    session.execute.return_value = found(orm)
    page = await sut.get_by_diagram(orm.diagram_id)
    assert page == DocumentationPage(
        id=orm.id, diagram_id=orm.diagram_id, content="# Old", created_at=NOW, updated_at=NOW
    )
    session.execute.return_value = found(None)
    assert await sut.get_by_diagram(uuid.uuid4()) is None


async def test_should_update_the_content_of_an_existing_page(
    sut: DocumentationPageRepositoryImpl, session: AsyncMock
) -> None:
    orm = page_orm()
    session.execute.return_value = found(orm)
    page = await sut.upsert(DocumentationPage(diagram_id=orm.diagram_id, content="# New"))
    assert orm.content == "# New"
    assert page.id == orm.id
    session.add.assert_not_called()
    session.commit.assert_awaited_once()


async def test_should_create_the_page_when_the_diagram_has_none(
    sut: DocumentationPageRepositoryImpl, session: AsyncMock
) -> None:
    session.execute.return_value = found(None)
    new = DocumentationPage(diagram_id=uuid.uuid4(), content="# First")
    page = await sut.upsert(new)
    added = session.add.call_args.args[0]
    assert (added.id, added.diagram_id, added.content) == (new.id, new.diagram_id, "# First")
    assert page.content == "# First"
    session.commit.assert_awaited_once()
