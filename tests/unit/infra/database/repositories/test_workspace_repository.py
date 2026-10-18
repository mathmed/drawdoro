import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from sqlalchemy.exc import IntegrityError

from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import ConflictError
from app.infra.database.models.workspace import WorkspaceORM
from app.infra.database.repositories.workspace_repository import (
    SLUG_CONSTRAINT,
    WorkspaceRepositoryImpl,
)

NOW = datetime(2026, 10, 1, 12, tzinfo=UTC)


def stamp(orm: WorkspaceORM) -> None:
    orm.created_at = orm.created_at or NOW
    orm.updated_at = orm.updated_at or NOW


def violation(error: UniqueViolationError | ForeignKeyViolationError, constraint: str) -> Exception:
    error.constraint_name = constraint
    return IntegrityError("INSERT INTO workspaces ...", None, error)


@pytest.fixture
def stored() -> WorkspaceORM:
    return WorkspaceORM(id=uuid.uuid4(), name="Acme", slug="acme", created_at=NOW, updated_at=NOW)


@pytest.fixture
def session(stored: WorkspaceORM) -> AsyncMock:
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.refresh.side_effect = stamp
    result = MagicMock()
    result.scalar_one.return_value = stored
    mock.execute.return_value = result
    return mock


@pytest.fixture
def sut(session: AsyncMock) -> WorkspaceRepositoryImpl:
    return WorkspaceRepositoryImpl(session)


async def test_should_create_the_workspace_and_commit(
    sut: WorkspaceRepositoryImpl, session: AsyncMock
) -> None:
    workspace = Workspace(name="Acme", slug="acme")
    created = await sut.create(workspace)
    added = session.add.call_args.args[0]
    assert (added.id, added.name, added.slug) == (workspace.id, "Acme", "acme")
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    assert (created.id, created.slug) == (workspace.id, "acme")


async def test_should_update_the_name_and_slug_and_commit(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, stored: WorkspaceORM
) -> None:
    updated = await sut.update(Workspace(id=stored.id, name="Acme Corp", slug="acme-corp"))
    assert (stored.name, stored.slug) == ("Acme Corp", "acme-corp")
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    assert (updated.name, updated.slug) == ("Acme Corp", "acme-corp")


async def test_should_raise_conflict_error_when_creating_with_a_taken_slug(
    sut: WorkspaceRepositoryImpl, session: AsyncMock
) -> None:
    session.commit.side_effect = violation(UniqueViolationError("duplicate"), SLUG_CONSTRAINT)
    with pytest.raises(ConflictError, match="^Another workspace already uses this slug$"):
        await sut.create(Workspace(name="Acme", slug="acme"))
    session.rollback.assert_awaited_once()
    session.refresh.assert_not_awaited()


async def test_should_raise_conflict_error_when_updating_to_a_taken_slug(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, stored: WorkspaceORM
) -> None:
    session.commit.side_effect = violation(UniqueViolationError("duplicate"), SLUG_CONSTRAINT)
    with pytest.raises(ConflictError, match="^Another workspace already uses this slug$"):
        await sut.update(Workspace(id=stored.id, name="Acme", slug="taken"))
    session.rollback.assert_awaited_once()
    session.refresh.assert_not_awaited()


@pytest.mark.parametrize(
    "error",
    [
        violation(UniqueViolationError("duplicate"), "workspaces_pkey"),
        violation(ForeignKeyViolationError("missing"), SLUG_CONSTRAINT),
    ],
    ids=["another-unique-constraint", "not-a-unique-violation"],
)
async def test_should_roll_back_and_propagate_other_integrity_errors(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, error: Exception
) -> None:
    session.commit.side_effect = error
    with pytest.raises(IntegrityError):
        await sut.create(Workspace(name="Acme", slug="acme"))
    session.rollback.assert_awaited_once()


@pytest.mark.parametrize(("found", "expected"), [(uuid.uuid4(), True), (None, False)])
async def test_should_check_existence_including_deleted_workspaces(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, found: uuid.UUID | None, expected: bool
) -> None:
    workspace_id = uuid.uuid4()
    result = MagicMock()
    result.scalar_one_or_none.return_value = found
    session.execute.return_value = result
    assert await sut.exists_including_deleted(workspace_id) is expected
    statement = session.execute.await_args.args[0]
    assert [column.name for column in statement.selected_columns] == ["id"]
    assert list(statement.compile().params.values()) == [workspace_id]
    assert "deleted_at" not in str(statement)
