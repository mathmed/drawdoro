import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.documentation.upsert_documentation_page import (
    UpsertDocumentationPage,
    UpsertDocumentationPageParams,
)
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DocumentationPageRepository)


@pytest.fixture
def diagrams() -> NonCallableMagicMock:
    mock = double(DiagramRepository)
    mock.exists.return_value = True
    return mock


@pytest.fixture
def sut(repo: NonCallableMagicMock, diagrams: NonCallableMagicMock) -> UpsertDocumentationPage:
    return UpsertDocumentationPage(repo, diagrams)


async def test_should_upsert_the_page_of_the_diagram(
    sut: UpsertDocumentationPage, repo: NonCallableMagicMock, diagrams: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.upsert.side_effect = lambda page: page
    result = await sut.execute(UpsertDocumentationPageParams(diagram_id=diagram_id, content="# Hi"))
    page = repo.upsert.await_args.args[0]
    assert result is page
    assert page.diagram_id == diagram_id
    assert page.content == "# Hi"
    diagrams.exists.assert_awaited_once_with(diagram_id)


async def test_should_raise_not_found_error_when_the_diagram_does_not_exist(
    sut: UpsertDocumentationPage, repo: NonCallableMagicMock, diagrams: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    diagrams.exists.return_value = False
    with pytest.raises(NotFoundError, match=f"^Diagram {diagram_id} not found$"):
        await sut.execute(UpsertDocumentationPageParams(diagram_id=diagram_id, content="# Hi"))
    repo.upsert.assert_not_awaited()
