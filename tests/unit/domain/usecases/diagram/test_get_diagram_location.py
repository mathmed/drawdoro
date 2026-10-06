import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram_location import (
    GetDiagramLocation,
    GetDiagramLocationParams,
)
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> GetDiagramLocation:
    return GetDiagramLocation(repo)


async def test_should_return_where_the_diagram_is(
    sut: GetDiagramLocation, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    location = DiagramLocation(workspace_id=uuid.uuid4(), project_id=uuid.uuid4())
    repo.get_location.return_value = location

    result = await sut.execute(GetDiagramLocationParams(diagram_id=diagram_id))

    assert result == location
    repo.get_location.assert_awaited_once_with(diagram_id)


async def test_should_raise_not_found_for_a_missing_diagram(
    sut: GetDiagramLocation, repo: NonCallableMagicMock
) -> None:
    repo.get_location.return_value = None
    with pytest.raises(NotFoundError, match="^Diagram not found$"):
        await sut.execute(GetDiagramLocationParams(diagram_id=uuid.uuid4()))
