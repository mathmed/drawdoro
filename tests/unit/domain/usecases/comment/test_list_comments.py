from unittest.mock import AsyncMock

import pytest

from app.domain.entities.models.comment import Comment
from app.domain.enums.comment_status import CommentStatus
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.comment.list_comments import ListComments, ListCommentsParams
from tests.unit.domain.usecases.comment.conftest import (
    ANA_ID,
    ANAS_AGENT,
    ANAS_KEY_ID,
    DIAGRAM_ID,
)

MINE = Comment(
    diagram_id=DIAGRAM_ID,
    content="Added X",
    author_id=ANA_ID,
    origin=RevisionOrigin.AGENT,
    api_key_id=ANAS_KEY_ID,
)
ANAS = Comment(diagram_id=DIAGRAM_ID, content="Missing X", author_id=ANA_ID)


@pytest.fixture
def sut(comments: AsyncMock, diagrams: AsyncMock) -> ListComments:
    comments.list_by_diagram.return_value = [ANAS, MINE]
    return ListComments(comments, diagrams)


async def test_should_flag_the_callers_own_comments(sut: ListComments) -> None:
    listed = await sut.execute(ListCommentsParams(diagram_id=DIAGRAM_ID, actor=ANAS_AGENT))
    assert [(c.id, c.created_by_you) for c in listed] == [(ANAS.id, False), (MINE.id, True)]


async def test_should_list_every_comment_by_default(sut: ListComments, comments: AsyncMock) -> None:
    await sut.execute(ListCommentsParams(diagram_id=DIAGRAM_ID))
    comments.list_by_diagram.assert_awaited_once_with(DIAGRAM_ID, CommentStatus.ALL)


async def test_should_filter_by_status(sut: ListComments, comments: AsyncMock) -> None:
    await sut.execute(ListCommentsParams(diagram_id=DIAGRAM_ID, status=CommentStatus.OPEN))
    comments.list_by_diagram.assert_awaited_once_with(DIAGRAM_ID, CommentStatus.OPEN)


async def test_should_report_missing_diagrams(
    sut: ListComments, comments: AsyncMock, diagrams: AsyncMock
) -> None:
    diagrams.exists.return_value = False
    with pytest.raises(NotFoundError, match=f"^Diagram {DIAGRAM_ID} not found$"):
        await sut.execute(ListCommentsParams(diagram_id=DIAGRAM_ID))
    diagrams.exists.assert_awaited_once_with(DIAGRAM_ID)
    comments.list_by_diagram.assert_not_awaited()
