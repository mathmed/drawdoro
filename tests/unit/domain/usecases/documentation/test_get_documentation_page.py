import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.entities.models.documentation_page import DocumentationPage
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.documentation.get_documentation_page import (
    GetDocumentationPage,
    GetDocumentationPageParams,
)
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DocumentationPageRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> GetDocumentationPage:
    return GetDocumentationPage(repo)


async def test_should_return_the_page_of_the_diagram(
    sut: GetDocumentationPage, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    expected = DocumentationPage(diagram_id=diagram_id, content="# Hi")
    repo.get_by_diagram.return_value = expected
    assert await sut.execute(GetDocumentationPageParams(diagram_id=diagram_id)) is expected
    repo.get_by_diagram.assert_awaited_once_with(diagram_id)


async def test_should_raise_not_found_error_when_the_diagram_has_no_page(
    sut: GetDocumentationPage, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_diagram.return_value = None
    with pytest.raises(
        NotFoundError, match=f"Documentation page for diagram {diagram_id} not found"
    ):
        await sut.execute(GetDocumentationPageParams(diagram_id=diagram_id))
