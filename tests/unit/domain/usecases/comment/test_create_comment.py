import logging
import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.entities.models.comment import Comment
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError
from app.domain.usecases.comment.create_comment import CreateComment, CreateCommentParams
from tests.unit.domain.usecases.comment.conftest import (
    ANA,
    ANA_ID,
    ANAS_AGENT,
    ANAS_KEY_ID,
    DIAGRAM_ID,
    OWNERLESS_AGENT,
)


@pytest.fixture
def sut(comments: AsyncMock, diagrams: AsyncMock, notifier: AsyncMock) -> CreateComment:
    return CreateComment(comments, diagrams, notifier)


def stored(comments: AsyncMock) -> Comment:
    comment: Comment = comments.create.await_args.args[0]
    return comment


async def test_should_store_a_persons_comment_on_a_shape(
    sut: CreateComment, comments: AsyncMock, diagrams: AsyncMock
) -> None:
    created = await sut.execute(
        CreateCommentParams(
            diagram_id=DIAGRAM_ID, element_id=" shape:a ", content="  Missing X  ", actor=ANA
        )
    )
    comment = stored(comments)
    assert (comment.diagram_id, comment.element_id, comment.content) == (
        DIAGRAM_ID,
        "shape:a",
        "Missing X",
    )
    assert (comment.author_id, comment.origin, comment.api_key_id) == (
        ANA_ID,
        RevisionOrigin.HUMAN,
        None,
    )
    assert (comment.agent_name, comment.agent_label) == (None, None)
    assert created.created_by_you is True
    assert created.id == comment.id
    diagrams.exists.assert_awaited_once_with(DIAGRAM_ID)


async def test_should_record_the_agent_and_its_key(sut: CreateComment, comments: AsyncMock) -> None:
    await sut.execute(CreateCommentParams(diagram_id=DIAGRAM_ID, content="Done", actor=ANAS_AGENT))
    comment = stored(comments)
    assert comment.origin == RevisionOrigin.AGENT
    assert (comment.author_id, comment.api_key_id) == (ANA_ID, ANAS_KEY_ID)
    assert (comment.agent_name, comment.agent_label) == ("Claude", "laptop")
    assert comment.element_id is None


async def test_should_not_let_agents_write_in_someone_elses_name(
    sut: CreateComment, comments: AsyncMock
) -> None:
    await sut.execute(
        CreateCommentParams(
            diagram_id=DIAGRAM_ID, content="Hi", actor=OWNERLESS_AGENT, author_id=uuid.uuid4()
        )
    )
    assert stored(comments).author_id is None


async def test_should_not_let_people_write_in_someone_elses_name(
    sut: CreateComment, comments: AsyncMock
) -> None:
    await sut.execute(
        CreateCommentParams(diagram_id=DIAGRAM_ID, content="Hi", actor=ANA, author_id=uuid.uuid4())
    )
    assert stored(comments).author_id == ANA_ID


async def test_should_take_the_named_author_when_auth_is_disabled(
    sut: CreateComment, comments: AsyncMock
) -> None:
    author_id = uuid.uuid4()
    await sut.execute(CreateCommentParams(diagram_id=DIAGRAM_ID, content="Hi", author_id=author_id))
    assert stored(comments).author_id == author_id


async def test_should_tell_open_editors(sut: CreateComment, notifier: AsyncMock) -> None:
    await sut.execute(CreateCommentParams(diagram_id=DIAGRAM_ID, content="Hi", actor=ANA))
    notifier.notify_changed.assert_awaited_once_with(DIAGRAM_ID)


async def test_should_log_who_commented_without_the_text(
    sut: CreateComment, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        created = await sut.execute(
            CreateCommentParams(diagram_id=DIAGRAM_ID, content="secret plan", actor=ANAS_AGENT)
        )
    assert caplog.messages == [
        f"Comment {created.id} created on diagram {DIAGRAM_ID} by {ANAS_AGENT.audit_label}"
    ]


async def test_should_reject_missing_diagrams(
    sut: CreateComment, comments: AsyncMock, diagrams: AsyncMock, notifier: AsyncMock
) -> None:
    diagrams.exists.return_value = False
    with pytest.raises(NotFoundError, match=f"^Diagram {DIAGRAM_ID} not found$"):
        await sut.execute(CreateCommentParams(diagram_id=DIAGRAM_ID, content="Hi", actor=ANA))
    comments.create.assert_not_awaited()
    notifier.notify_changed.assert_not_awaited()


async def test_should_reject_empty_comments(sut: CreateComment, comments: AsyncMock) -> None:
    with pytest.raises(InvalidInputError):
        await sut.execute(CreateCommentParams(diagram_id=DIAGRAM_ID, content=" \n", actor=ANA))
    comments.create.assert_not_awaited()


async def test_should_reject_oversized_element_ids(sut: CreateComment, comments: AsyncMock) -> None:
    with pytest.raises(InvalidInputError):
        await sut.execute(
            CreateCommentParams(diagram_id=DIAGRAM_ID, content="Hi", element_id="s" * 300)
        )
    comments.create.assert_not_awaited()
