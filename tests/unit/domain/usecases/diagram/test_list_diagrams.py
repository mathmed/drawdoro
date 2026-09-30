import uuid
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram_summary import DiagramSummary
from app.domain.usecases.diagram.list_diagrams import ListDiagrams, ListDiagramsParams


@pytest.fixture
def repo() -> DiagramRepository:
    return cast(DiagramRepository, create_autospec(DiagramRepository))


@pytest.fixture
def sut(repo: DiagramRepository) -> ListDiagrams:
    return ListDiagrams(repo)


async def test_should_list_diagram_summaries_of_the_project(
    sut: ListDiagrams, repo: DiagramRepository
) -> None:
    project_id = uuid.uuid4()
    now = datetime.now(UTC)
    summary = DiagramSummary(
        id=uuid.uuid4(), project_id=project_id, name="Payments", created_at=now, updated_at=now
    )
    repo.list_by_project = AsyncMock(return_value=[summary])  # type: ignore[method-assign]

    assert await sut.execute(ListDiagramsParams(project_id=project_id)) == [summary]
    repo.list_by_project.assert_awaited_once_with(project_id)
