import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram_by_share_token import (
    GetDiagramByShareToken,
    GetDiagramByShareTokenParams,
)
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> GetDiagramByShareToken:
    return GetDiagramByShareToken(repo)


async def test_should_return_diagram_for_valid_token(
    sut: GetDiagramByShareToken, repo: NonCallableMagicMock
) -> None:
    diagram = Diagram(id=uuid.uuid4(), project_id=uuid.uuid4(), name="Shared", share_token="tok")
    repo.get_by_share_token.return_value = diagram

    result = await sut.execute(GetDiagramByShareTokenParams(share_token="tok"))

    assert result.id == diagram.id
    repo.get_by_share_token.assert_awaited_once_with("tok")


async def test_should_raise_not_found_for_unknown_token(
    sut: GetDiagramByShareToken, repo: NonCallableMagicMock
) -> None:
    repo.get_by_share_token.return_value = None
    with pytest.raises(NotFoundError):
        await sut.execute(GetDiagramByShareTokenParams(share_token="missing"))
