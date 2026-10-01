import logging
import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.usecases.comment.delete_comment import DeleteComment, DeleteCommentParams
from tests.unit.domain.usecases.comment.conftest import (
    ANA,
    ANA_ID,
    ANAS_AGENT,
    ANAS_KEY_ID,
    DIAGRAM_ID,
    OWNERLESS_AGENT,
)

PERSONS = Comment(diagram_id=DIAGRAM_ID, content="Missing X", author_id=uuid.uuid4())
ANAS_AGENTS = Comment(
    diagram_id=DIAGRAM_ID,
    content="Added X",
    author_id=ANA_ID,
    origin=RevisionOrigin.AGENT,
    api_key_id=ANAS_KEY_ID,
)


@pytest.fixture
def sut(comments: AsyncMock, notifier: AsyncMock) -> DeleteComment:
    return DeleteComment(comments, notifier)


async def test_should_let_an_agent_delete_its_own_comment(
    sut: DeleteComment, comments: AsyncMock, notifier: AsyncMock
) -> None:
    comments.get.return_value = ANAS_AGENTS
    await sut.execute(
        DeleteCommentParams(diagram_id=DIAGRAM_ID, comment_id=ANAS_AGENTS.id, actor=ANAS_AGENT)
    )
    comments.get.assert_awaited_once_with(DIAGRAM_ID, ANAS_AGENTS.id)
    comments.delete.assert_awaited_once_with(ANAS_AGENTS.id)
    notifier.notify_changed.assert_awaited_once_with(DIAGRAM_ID)


@pytest.mark.parametrize("actor", [ANAS_AGENT, OWNERLESS_AGENT], ids=["keyed", "ownerless"])
async def test_should_not_let_agents_delete_what_they_did_not_write(
    sut: DeleteComment, comments: AsyncMock, notifier: AsyncMock, actor: CommentActor
) -> None:
    comments.get.return_value = PERSONS
    with pytest.raises(ForbiddenError) as error:
        await sut.execute(
            DeleteCommentParams(diagram_id=DIAGRAM_ID, comment_id=PERSONS.id, actor=actor)
        )
    assert error.value.message == (
        "Agents can only delete comments written with their own API key. "
        "Resolve this comment instead, or ask a person to delete it"
    )
    comments.delete.assert_not_awaited()
    notifier.notify_changed.assert_not_awaited()


async def test_should_let_people_delete_any_comment(
    sut: DeleteComment, comments: AsyncMock
) -> None:
    comments.get.return_value = ANAS_AGENTS
    await sut.execute(
        DeleteCommentParams(
            diagram_id=DIAGRAM_ID, comment_id=ANAS_AGENTS.id, actor=ANA.model_copy()
        )
    )
    comments.delete.assert_awaited_once_with(ANAS_AGENTS.id)


async def test_should_report_comments_missing_from_the_diagram(
    sut: DeleteComment, comments: AsyncMock
) -> None:
    comments.get.return_value = None
    comment_id = uuid.uuid4()
    with pytest.raises(NotFoundError, match=f"^Comment {comment_id} not found in this diagram$"):
        await sut.execute(DeleteCommentParams(diagram_id=DIAGRAM_ID, comment_id=comment_id))
    comments.delete.assert_not_awaited()


async def test_should_log_who_deleted_it(
    sut: DeleteComment, comments: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    comments.get.return_value = ANAS_AGENTS
    with caplog.at_level(logging.INFO):
        await sut.execute(
            DeleteCommentParams(diagram_id=DIAGRAM_ID, comment_id=ANAS_AGENTS.id, actor=ANAS_AGENT)
        )
    assert caplog.messages == [
        f"Comment {ANAS_AGENTS.id} deleted from diagram {DIAGRAM_ID} by {ANAS_AGENT.audit_label}"
    ]
