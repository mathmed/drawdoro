import uuid
from datetime import UTC, datetime
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram_summary import DiagramSummary
from app.domain.usecases.diagram.list_diagrams import ListDiagrams, ListDiagramsParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ListDiagrams:
    return ListDiagrams(repo)


async def test_should_list_diagram_summaries_of_the_project(
    sut: ListDiagrams, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    now = datetime.now(UTC)
    summary = DiagramSummary(
        id=uuid.uuid4(), project_id=project_id, name="Payments", created_at=now, updated_at=now
    )
    repo.list_by_project.return_value = [summary]

    assert await sut.execute(ListDiagramsParams(project_id=project_id)) == [summary]
    repo.list_by_project.assert_awaited_once_with(project_id)
