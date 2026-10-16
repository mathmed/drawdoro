import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.repositories.folder_repository import FolderRepositoryImpl
from app.infra.database.repositories.project_repository import ProjectRepositoryImpl
from app.infra.database.repositories.workspace_repository import WorkspaceRepositoryImpl


class SoftDeleteRepository(Protocol):
    async def delete(self, entity_id: uuid.UUID, /) -> None: ...


@pytest.fixture
def row() -> MagicMock:
    return MagicMock(deleted_at=None)


@pytest.fixture
def session(row: MagicMock) -> AsyncMock:
    session = AsyncMock()
    session.delete = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = row
    session.execute.return_value = result
    return session


@pytest.fixture(
    params=[
        WorkspaceRepositoryImpl,
        ProjectRepositoryImpl,
        FolderRepositoryImpl,
        DiagramRepositoryImpl,
    ]
)
def sut(request: pytest.FixtureRequest, session: AsyncMock) -> SoftDeleteRepository:
    repository: Callable[[AsyncSession], SoftDeleteRepository] = request.param
    return repository(session)


async def test_should_soft_delete_the_live_row_with_the_current_utc_instant(
    sut: SoftDeleteRepository, session: AsyncMock, row: MagicMock
) -> None:
    entity_id = uuid.uuid4()
    before = datetime.now(UTC)

    await sut.delete(entity_id)

    deleted_at = row.deleted_at
    assert isinstance(deleted_at, datetime)
    assert deleted_at.utcoffset() == timedelta(0)
    assert before <= deleted_at <= datetime.now(UTC)
    statement = session.execute.await_args.args[0]
    assert "deleted_at IS NULL" in str(statement)
    assert entity_id in statement.compile().params.values()
    session.delete.assert_not_awaited()
    session.commit.assert_awaited_once()


async def test_should_not_soft_delete_a_missing_or_already_deleted_row_again(
    sut: SoftDeleteRepository, session: AsyncMock
) -> None:
    session.execute.return_value.scalar_one.side_effect = NoResultFound()

    with pytest.raises(NoResultFound):
        await sut.delete(uuid.uuid4())

    session.commit.assert_not_awaited()
