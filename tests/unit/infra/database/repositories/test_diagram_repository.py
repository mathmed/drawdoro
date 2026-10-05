import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities.models.diagram_summary import DiagramSummary
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl


class Row:
    def __init__(self, **values: Any) -> None:
        self._values = values

    def _asdict(self) -> dict[str, Any]:
        return self._values


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sut(session: AsyncMock) -> DiagramRepositoryImpl:
    return DiagramRepositoryImpl(session)


async def test_should_list_project_diagrams_without_loading_their_content(
    sut: DiagramRepositoryImpl, session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    now = datetime.now(UTC)
    row = Row(
        id=uuid.uuid4(),
        project_id=project_id,
        folder_id=None,
        name="Payments",
        created_at=now,
        updated_at=now,
    )
    result = MagicMock()
    result.all.return_value = [row]
    session.execute.return_value = result

    diagrams = await sut.list_by_project(project_id)

    assert diagrams == [DiagramSummary.model_validate(row._asdict())]
    statement = session.execute.await_args.args[0]
    selected = {column.name for column in statement.selected_columns}
    assert selected == {"id", "project_id", "folder_id", "name", "created_at", "updated_at"}


@pytest.mark.parametrize(("found", "expected"), [(uuid.uuid4(), True), (None, False)])
async def test_should_check_existence_without_loading_the_canvas(
    sut: DiagramRepositoryImpl, session: AsyncMock, found: uuid.UUID | None, expected: bool
) -> None:
    result = MagicMock()
    result.scalar_one_or_none.return_value = found
    session.execute.return_value = result
    assert await sut.exists(uuid.uuid4()) is expected
    statement = session.execute.await_args.args[0]
    assert [column.name for column in statement.selected_columns] == ["id"]
    assert "deleted_at IS NULL" in str(statement)


async def test_should_locate_a_live_diagram_in_one_query_without_its_content(
    sut: DiagramRepositoryImpl, session: AsyncMock
) -> None:
    workspace_id, project_id = uuid.uuid4(), uuid.uuid4()
    result = MagicMock()
    result.one_or_none.return_value = MagicMock(workspace_id=workspace_id, project_id=project_id)
    session.execute.return_value = result

    location = await sut.get_location(uuid.uuid4())

    assert location == DiagramLocation(workspace_id=workspace_id, project_id=project_id)
    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    assert [column.name for column in statement.selected_columns] == ["workspace_id", "project_id"]
    sql = str(statement)
    assert "JOIN projects" in sql
    assert "diagrams.deleted_at IS NULL" in sql
    assert "projects.deleted_at IS NULL" in sql


async def test_should_not_locate_a_missing_diagram(
    sut: DiagramRepositoryImpl, session: AsyncMock
) -> None:
    result = MagicMock()
    result.one_or_none.return_value = None
    session.execute.return_value = result
    assert await sut.get_location(uuid.uuid4()) is None
