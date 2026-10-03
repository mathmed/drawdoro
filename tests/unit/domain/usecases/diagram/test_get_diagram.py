import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram import GetDiagram, GetDiagramParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> GetDiagram:
    return GetDiagram(repo)


async def test_should_return_diagram_when_found(
    sut: GetDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    project_id = uuid.uuid4()
    expected = Diagram(id=diagram_id, project_id=project_id, name="My Diagram")
    repo.get_by_id.return_value = expected
    result = await sut.execute(GetDiagramParams(diagram_id=diagram_id))
    assert result.id == diagram_id
    assert result.name == "My Diagram"
    repo.get_by_id.assert_awaited_once_with(diagram_id)


async def test_should_raise_not_found_error_when_diagram_missing(
    sut: GetDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=str(diagram_id)):
        await sut.execute(GetDiagramParams(diagram_id=diagram_id))
