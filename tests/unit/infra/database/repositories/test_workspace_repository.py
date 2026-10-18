import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from asyncpg.exceptions import PostgresError
from sqlalchemy import Table, UniqueConstraint
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_connection
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import ConflictError
from app.infra.database.models.workspace import WorkspaceORM
from app.infra.database.repositories.workspace_repository import WorkspaceRepositoryImpl

NOW = datetime(2026, 10, 1, 12, tzinfo=UTC)

# The ErrorResponse fields Postgres 17 sends when a workspace repeats a slug, captured from a
# database migrated by alembic. "n" is the constraint's name, which depends on how the database was
# created.
SLUG_TAKEN = {
    "S": "ERROR",
    "V": "ERROR",
    "C": "23505",
    "M": 'duplicate key value violates unique constraint "workspaces_slug_key"',
    "D": "Key (slug)=(acme) already exists.",
    "s": "public",
    "t": "workspaces",
    "n": "workspaces_slug_key",
    "F": "nbtinsert.c",
    "L": "666",
    "R": "_bt_check_unique",
}
# Same capture, for a workspace without a name.
NAME_MISSING = {
    "S": "ERROR",
    "V": "ERROR",
    "C": "23502",
    "M": 'null value in column "name" of relation "workspaces" violates not-null constraint',
    "s": "public",
    "t": "workspaces",
    "c": "name",
}


# What the session raises for those fields: asyncpg builds its error from them, as it does with the
# server's message, and SQLAlchemy's asyncpg dialect translates and wraps it as it does on a commit.
def database_error(fields: dict[str, str]) -> IntegrityError:
    dbapi = create_async_engine("postgresql+asyncpg://localhost/drawdoro").dialect.loaded_dbapi
    try:
        AsyncAdapt_asyncpg_connection._handle_exception_no_connection(
            dbapi, PostgresError.new(fields)
        )
    except dbapi.Error as translated:
        error = DBAPIError.instance("INSERT INTO workspaces ...", None, translated, dbapi.Error)
        assert isinstance(error, IntegrityError)
        return error
    raise AssertionError("the dialect did not translate the error")


def stamp(orm: WorkspaceORM) -> None:
    orm.created_at = orm.created_at or NOW
    orm.updated_at = orm.updated_at or NOW


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


@pytest.mark.parametrize(
    "constraint", ["workspaces_slug_key", "uq_workspaces_slug"], ids=["postgres-name", "other-name"]
)
async def test_should_raise_conflict_error_when_creating_with_a_taken_slug(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, constraint: str
) -> None:
    session.commit.side_effect = database_error(SLUG_TAKEN | {"n": constraint})
    with pytest.raises(ConflictError, match="^Another workspace already uses this slug$"):
        await sut.create(Workspace(name="Acme", slug="acme"))
    session.rollback.assert_awaited_once()
    session.refresh.assert_not_awaited()


async def test_should_raise_conflict_error_when_updating_to_a_taken_slug(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, stored: WorkspaceORM
) -> None:
    session.commit.side_effect = database_error(SLUG_TAKEN)
    with pytest.raises(ConflictError, match="^Another workspace already uses this slug$"):
        await sut.update(Workspace(id=stored.id, name="Acme", slug="taken"))
    session.rollback.assert_awaited_once()
    session.refresh.assert_not_awaited()


@pytest.mark.parametrize(
    "fields",
    [
        NAME_MISSING,
        SLUG_TAKEN | {"t": "workspace_members"},
        SLUG_TAKEN | {"C": "23503"},
    ],
    ids=["not-a-unique-violation", "unique-violation-of-another-table", "foreign-key-violation"],
)
async def test_should_roll_back_and_propagate_other_integrity_errors(
    sut: WorkspaceRepositoryImpl, session: AsyncMock, fields: dict[str, str]
) -> None:
    session.commit.side_effect = database_error(fields)
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


# A unique violation on workspaces is read as a taken slug: another unique column would need
# telling apart.
def test_should_keep_the_slug_as_the_only_unique_column_besides_the_id() -> None:
    table = WorkspaceORM.__table__
    assert isinstance(table, Table)
    unique = {tuple(column.name for column in table.primary_key.columns)}
    unique |= {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    unique |= {
        tuple(column.name for column in index.columns) for index in table.indexes if index.unique
    }
    assert unique == {("id",), ("slug",)}
