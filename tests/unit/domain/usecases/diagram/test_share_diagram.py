import uuid
from typing import cast
from unittest.mock import ANY, AsyncMock, create_autospec

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.share_diagram import ShareDiagram, ShareDiagramParams


@pytest.fixture
def repo() -> DiagramRepository:
    return cast(DiagramRepository, create_autospec(DiagramRepository))


@pytest.fixture
def sut(repo: DiagramRepository) -> ShareDiagram:
    return ShareDiagram(repo)


async def test_should_generate_share_token_when_missing(
    sut: ShareDiagram, repo: DiagramRepository
) -> None:
    diagram_id = uuid.uuid4()
    diagram = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="Diagram", share_token=None)
    shared = diagram.model_copy(update={"share_token": "generated"})
    repo.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    repo.set_share_token = AsyncMock(return_value=shared)  # type: ignore[method-assign]

    result = await sut.execute(ShareDiagramParams(diagram_id=diagram_id))

    assert result.share_token == "generated"
    repo.set_share_token.assert_awaited_once_with(diagram_id, ANY)


async def test_should_reuse_existing_share_token(
    sut: ShareDiagram, repo: DiagramRepository
) -> None:
    diagram_id = uuid.uuid4()
    diagram = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="Diagram", share_token="abc123")
    repo.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    repo.set_share_token = AsyncMock()  # type: ignore[method-assign]

    result = await sut.execute(ShareDiagramParams(diagram_id=diagram_id))

    assert result.share_token == "abc123"
    repo.set_share_token.assert_not_awaited()


async def test_should_raise_not_found_when_diagram_missing(
    sut: ShareDiagram, repo: DiagramRepository
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError, match=str(diagram_id)):
        await sut.execute(ShareDiagramParams(diagram_id=diagram_id))
