import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.revision.get_diagram_revision import (
    GetDiagramRevision,
    GetDiagramRevisionParams,
)
from app.domain.usecases.revision.list_diagram_revisions import (
    MAX_LISTED_REVISIONS,
    ListDiagramRevisions,
    ListDiagramRevisionsParams,
)
from tests.doubles import double

DIAGRAM_ID = uuid.uuid4()


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRevisionRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ListDiagramRevisions:
    return ListDiagramRevisions(repo)


@pytest.mark.parametrize(
    ("requested", "expected"), [(10, 10), (0, 1), (10_000, MAX_LISTED_REVISIONS)]
)
async def test_should_list_revisions_within_the_limit(
    sut: ListDiagramRevisions, repo: NonCallableMagicMock, requested: int, expected: int
) -> None:
    revisions = [DiagramRevision(diagram_id=DIAGRAM_ID)]
    repo.list_by_diagram.return_value = revisions
    result = await sut.execute(ListDiagramRevisionsParams(diagram_id=DIAGRAM_ID, limit=requested))
    assert result == revisions
    repo.list_by_diagram.assert_awaited_once_with(DIAGRAM_ID, expected)


async def test_should_get_a_revision_of_the_diagram(repo: NonCallableMagicMock) -> None:
    revision = DiagramRevision(diagram_id=DIAGRAM_ID)
    repo.get.return_value = revision
    params = GetDiagramRevisionParams(diagram_id=DIAGRAM_ID, revision_id=revision.id)
    assert await GetDiagramRevision(repo).execute(params) == revision
    repo.get.assert_awaited_once_with(DIAGRAM_ID, revision.id)


async def test_should_raise_not_found_for_missing_revision(
    repo: NonCallableMagicMock,
) -> None:
    repo.get.return_value = None
    params = GetDiagramRevisionParams(diagram_id=DIAGRAM_ID, revision_id=uuid.uuid4())
    with pytest.raises(NotFoundError, match=f"^Revision {params.revision_id} not found$"):
        await GetDiagramRevision(repo).execute(params)
