import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities.models.diagram_summary import DiagramSummary
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
