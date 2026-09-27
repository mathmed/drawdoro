import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram import GetDiagram, GetDiagramParams


@pytest.fixture
def repo() -> DiagramRepository:
    return cast(DiagramRepository, create_autospec(DiagramRepository))


@pytest.fixture
def sut(repo: DiagramRepository) -> GetDiagram:
    return GetDiagram(repo)


async def test_should_return_diagram_when_found(sut: GetDiagram, repo: DiagramRepository) -> None:
    diagram_id = uuid.uuid4()
    project_id = uuid.uuid4()
    expected = Diagram(id=diagram_id, project_id=project_id, name="My Diagram")
    repo.get_by_id = AsyncMock(return_value=expected)  # type: ignore[method-assign]
    result = await sut.execute(GetDiagramParams(diagram_id=diagram_id))
    assert result.id == diagram_id
    assert result.name == "My Diagram"
    repo.get_by_id.assert_awaited_once_with(diagram_id)


async def test_should_raise_not_found_error_when_diagram_missing(
    sut: GetDiagram, repo: DiagramRepository
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError, match=str(diagram_id)):
        await sut.execute(GetDiagramParams(diagram_id=diagram_id))
