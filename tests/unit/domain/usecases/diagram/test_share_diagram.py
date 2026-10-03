import uuid
from unittest.mock import ANY, AsyncMock, NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.share_diagram import ShareDiagram, ShareDiagramParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ShareDiagram:
    return ShareDiagram(repo)


async def test_should_generate_share_token_when_missing(
    sut: ShareDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    diagram = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="Diagram", share_token=None)
    shared = diagram.model_copy(update={"share_token": "generated"})
    repo.get_by_id.return_value = diagram
    repo.set_share_token.return_value = shared

    result = await sut.execute(ShareDiagramParams(diagram_id=diagram_id))

    assert result.share_token == "generated"
    repo.set_share_token.assert_awaited_once_with(diagram_id, ANY)


async def test_should_reuse_existing_share_token(
    sut: ShareDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    diagram = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="Diagram", share_token="abc123")
    repo.get_by_id.return_value = diagram
    repo.set_share_token = AsyncMock()

    result = await sut.execute(ShareDiagramParams(diagram_id=diagram_id))

    assert result.share_token == "abc123"
    repo.set_share_token.assert_not_awaited()


async def test_should_raise_not_found_when_diagram_missing(
    sut: ShareDiagram, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=str(diagram_id)):
        await sut.execute(ShareDiagramParams(diagram_id=diagram_id))
