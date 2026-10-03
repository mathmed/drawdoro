import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.entities.models.comment import Comment
from app.domain.enums.comment_status import CommentStatus
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import NotFoundError
from app.infra.database.models.comment import CommentORM
from app.infra.database.repositories.comment_repository import CommentRepositoryImpl

DIAGRAM_ID = uuid.uuid4()
KEY_ID = uuid.uuid4()
# The dialect the API runs on, so the SQL is checked as Postgres will receive it.
POSTGRES = create_async_engine("postgresql+asyncpg://").dialect


def orm(**values: object) -> CommentORM:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "diagram_id": DIAGRAM_ID,
        "element_id": "shape:a",
        "content": "Missing X",
        "author_id": uuid.uuid4(),
        "origin": "agent",
        "agent_name": "Claude",
        "agent_label": "laptop",
        "api_key_id": KEY_ID,
        "created_at": datetime(2026, 9, 30, 10),
        "resolved_at": datetime(2026, 9, 30, 11, tzinfo=UTC),
        "resolved_by_id": uuid.uuid4(),
        "resolved_by_origin": "human",
        "resolved_by_agent_name": None,
        "resolved_by_agent_label": None,
    }
    return CommentORM(**(defaults | values))


def rows(*results: tuple[CommentORM, str | None, str | None]) -> MagicMock:
    result = MagicMock()
    result.all.return_value = list(results)
    result.one_or_none.return_value = results[0] if results else None
    return result


def sql(session: AsyncMock) -> str:
    statement = session.execute.await_args.args[0]
    return str(statement.compile(dialect=POSTGRES))


@pytest.fixture
def session() -> AsyncMock:
    mock = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def sut(session: AsyncMock) -> CommentRepositoryImpl:
    return CommentRepositoryImpl(session)


async def test_should_map_authorship_and_resolution(
    sut: CommentRepositoryImpl, session: AsyncMock
) -> None:
    stored = orm()
    session.execute.return_value = rows((stored, "Ana", "Bruno"))
    [comment] = await sut.list_by_diagram(DIAGRAM_ID)
    assert comment.model_dump() == {
        "id": stored.id,
        "diagram_id": DIAGRAM_ID,
        "element_id": "shape:a",
        "content": "Missing X",
        "author_id": stored.author_id,
        "author_name": "Ana",
        "origin": RevisionOrigin.AGENT,
        "agent_name": "Claude",
        "agent_label": "laptop",
        "api_key_id": KEY_ID,
        "created_at": datetime(2026, 9, 30, 10),
        "resolved_at": datetime(2026, 9, 30, 11, tzinfo=UTC),
        "resolved_by_id": stored.resolved_by_id,
        "resolved_by_name": "Bruno",
        "resolved_by_origin": RevisionOrigin.HUMAN,
        "resolved_by_agent_name": None,
        "resolved_by_agent_label": None,
        "created_by_you": False,
    }


async def test_should_map_open_comments(sut: CommentRepositoryImpl, session: AsyncMock) -> None:
    session.execute.return_value = rows(
        (orm(resolved_at=None, resolved_by_origin=None), None, None)
    )
    [comment] = await sut.list_by_diagram(DIAGRAM_ID)
    assert (comment.is_resolved, comment.resolved_by_origin) == (False, None)


@pytest.mark.parametrize(
    ("status", "expected", "unexpected"),
    [
        (CommentStatus.OPEN, "comments.resolved_at IS NULL", "IS NOT NULL"),
        (CommentStatus.RESOLVED, "comments.resolved_at IS NOT NULL", "resolved_at IS NULL"),
        (CommentStatus.ALL, "comments.diagram_id", "resolved_at IS"),
    ],
)
async def test_should_filter_by_status(
    sut: CommentRepositoryImpl,
    session: AsyncMock,
    status: CommentStatus,
    expected: str,
    unexpected: str,
) -> None:
    session.execute.return_value = rows()
    await sut.list_by_diagram(DIAGRAM_ID, status)
    query = sql(session)
    assert expected in query
    assert unexpected not in query.split("WHERE", 1)[1]
    assert "ORDER BY comments.created_at" in query


async def test_should_only_get_comments_of_the_given_diagram(
    sut: CommentRepositoryImpl, session: AsyncMock
) -> None:
    session.execute.return_value = rows()
    assert await sut.get(DIAGRAM_ID, uuid.uuid4()) is None
    query = sql(session)
    assert "comments.id = " in query
    assert "comments.diagram_id = " in query


async def test_should_create_with_agent_authorship(
    sut: CommentRepositoryImpl, session: AsyncMock
) -> None:
    comment = Comment(
        diagram_id=DIAGRAM_ID,
        content="Added X",
        origin=RevisionOrigin.AGENT,
        agent_name="Claude",
        api_key_id=KEY_ID,
    )
    session.execute.return_value = rows((orm(id=comment.id), None, None))
    created = await sut.create(comment)
    added: CommentORM = session.add.call_args.args[0]
    assert (added.id, added.origin, added.agent_name, added.api_key_id) == (
        comment.id,
        RevisionOrigin.AGENT,
        "Claude",
        KEY_ID,
    )
    session.commit.assert_awaited_once()
    assert created.id == comment.id


async def test_should_save_the_resolution(sut: CommentRepositoryImpl, session: AsyncMock) -> None:
    stored = orm(resolved_at=None, resolved_by_id=None, resolved_by_origin=None)
    session.get.return_value = stored
    session.execute.return_value = rows((stored, None, "Ana"))
    resolver = uuid.uuid4()
    when = datetime(2026, 10, 1, tzinfo=UTC)
    comment = Comment(
        id=stored.id,
        diagram_id=DIAGRAM_ID,
        content="x",
        resolved_at=when,
        resolved_by_id=resolver,
        resolved_by_origin=RevisionOrigin.AGENT,
        resolved_by_agent_name="Claude",
        resolved_by_agent_label="laptop",
    )
    updated = await sut.update_resolution(comment)
    assert (stored.resolved_at, stored.resolved_by_id, stored.resolved_by_origin) == (
        when,
        resolver,
        RevisionOrigin.AGENT,
    )
    assert (stored.resolved_by_agent_name, stored.resolved_by_agent_label) == ("Claude", "laptop")
    session.commit.assert_awaited_once()
    assert updated.resolved_by_name == "Ana"


async def test_should_report_resolving_a_vanished_comment(
    sut: CommentRepositoryImpl, session: AsyncMock
) -> None:
    session.get.return_value = None
    with pytest.raises(NotFoundError):
        await sut.update_resolution(Comment(diagram_id=DIAGRAM_ID, content="x"))


async def test_should_delete_and_ignore_vanished_comments(
    sut: CommentRepositoryImpl, session: AsyncMock
) -> None:
    stored = orm()
    session.get.return_value = stored
    await sut.delete(stored.id)
    session.delete.assert_awaited_once_with(stored)
    session.get.return_value = None
    await sut.delete(uuid.uuid4())
    session.commit.assert_awaited_once()


async def test_should_report_a_comment_gone_right_after_writing(
    sut: CommentRepositoryImpl, session: AsyncMock
) -> None:
    session.execute.return_value = rows()
    with pytest.raises(NotFoundError):
        await sut.create(Comment(diagram_id=DIAGRAM_ID, content="x"))
