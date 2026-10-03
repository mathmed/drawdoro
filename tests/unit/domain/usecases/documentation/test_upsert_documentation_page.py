import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.usecases.documentation.upsert_documentation_page import (
    UpsertDocumentationPage,
    UpsertDocumentationPageParams,
)
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DocumentationPageRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> UpsertDocumentationPage:
    return UpsertDocumentationPage(repo)


async def test_should_upsert_the_page_of_the_diagram(
    sut: UpsertDocumentationPage, repo: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.upsert.side_effect = lambda page: page
    result = await sut.execute(UpsertDocumentationPageParams(diagram_id=diagram_id, content="# Hi"))
    page = repo.upsert.await_args.args[0]
    assert result is page
    assert page.diagram_id == diagram_id
    assert page.content == "# Hi"
