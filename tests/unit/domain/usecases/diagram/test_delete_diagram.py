import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.delete_diagram import DeleteDiagram, DeleteDiagramParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> DeleteDiagram:
    return DeleteDiagram(repo)


async def test_should_delete_the_diagram_when_found(
    sut: DeleteDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id.return_value = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="D")
    await sut.execute(DeleteDiagramParams(diagram_id=diagram_id))
    repo.get_by_id.assert_awaited_once_with(diagram_id)
    repo.delete.assert_awaited_once_with(diagram_id)


async def test_should_raise_not_found_error_when_the_diagram_is_missing(
    sut: DeleteDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Diagram {diagram_id} not found"):
        await sut.execute(DeleteDiagramParams(diagram_id=diagram_id))
    repo.delete.assert_not_awaited()
