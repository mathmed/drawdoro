import logging
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.comment.update_comment_resolution import (
    UpdateCommentResolution,
    UpdateCommentResolutionParams,
)
from tests.unit.domain.usecases.comment.conftest import (
    ANA,
    ANA_ID,
    ANAS_AGENT,
    DIAGRAM_ID,
)

BRUNO_ID = uuid.uuid4()
OPEN = Comment(diagram_id=DIAGRAM_ID, content="Missing X", author_id=BRUNO_ID)
RESOLVED = OPEN.model_copy(
    update={
        "resolved_at": datetime(2026, 9, 30, tzinfo=UTC),
        "resolved_by_id": BRUNO_ID,
        "resolved_by_name": "Bruno",
        "resolved_by_origin": RevisionOrigin.HUMAN,
        "resolved_by_agent_name": "Claude",
        "resolved_by_agent_label": "desk",
    }
)


@pytest.fixture
def sut(comments: AsyncMock, notifier: AsyncMock) -> UpdateCommentResolution:
    return UpdateCommentResolution(comments, notifier)


def params(resolved: bool, actor: CommentActor = ANAS_AGENT) -> UpdateCommentResolutionParams:
    return UpdateCommentResolutionParams(
        diagram_id=DIAGRAM_ID, comment_id=OPEN.id, resolved=resolved, actor=actor
    )


async def test_should_let_an_agent_resolve_someone_elses_comment(
    sut: UpdateCommentResolution, comments: AsyncMock, notifier: AsyncMock
) -> None:
    comments.get.return_value = OPEN
    before = datetime.now(UTC)
    resolved = await sut.execute(params(True))
    saved: Comment = comments.update_resolution.await_args.args[0]
    assert saved.id == OPEN.id
    assert saved.resolved_at is not None
    assert before <= saved.resolved_at <= datetime.now(UTC) + timedelta(seconds=1)
    assert saved.resolved_at.tzinfo is not None
    assert (saved.resolved_by_id, saved.resolved_by_origin) == (ANA_ID, RevisionOrigin.AGENT)
    assert (saved.resolved_by_agent_name, saved.resolved_by_agent_label) == ("Claude", "laptop")
    assert (resolved.is_resolved, resolved.created_by_you) == (True, False)
    comments.get.assert_awaited_once_with(DIAGRAM_ID, OPEN.id)
    notifier.notify_changed.assert_awaited_once_with(DIAGRAM_ID)


async def test_should_record_people_as_resolvers(
    sut: UpdateCommentResolution, comments: AsyncMock
) -> None:
    comments.get.return_value = OPEN
    await sut.execute(params(True, ANA))
    saved: Comment = comments.update_resolution.await_args.args[0]
    assert (saved.resolved_by_id, saved.resolved_by_origin) == (ANA_ID, RevisionOrigin.HUMAN)
    assert (saved.resolved_by_agent_name, saved.resolved_by_agent_label) == (None, None)


async def test_should_reopen_and_forget_the_resolver(
    sut: UpdateCommentResolution, comments: AsyncMock, notifier: AsyncMock
) -> None:
    comments.get.return_value = RESOLVED
    reopened = await sut.execute(params(False))
    saved: Comment = comments.update_resolution.await_args.args[0]
    assert saved.id == OPEN.id
    assert saved.model_dump(
        include={
            "resolved_at",
            "resolved_by_id",
            "resolved_by_name",
            "resolved_by_origin",
            "resolved_by_agent_name",
            "resolved_by_agent_label",
        }
    ) == dict.fromkeys(
        [
            "resolved_at",
            "resolved_by_id",
            "resolved_by_name",
            "resolved_by_origin",
            "resolved_by_agent_name",
            "resolved_by_agent_label",
        ]
    )
    assert reopened.is_resolved is False
    notifier.notify_changed.assert_awaited_once_with(DIAGRAM_ID)


@pytest.mark.parametrize(("current", "resolved"), [(OPEN, False), (RESOLVED, True)])
async def test_should_leave_comments_already_in_that_state_alone(
    sut: UpdateCommentResolution,
    comments: AsyncMock,
    notifier: AsyncMock,
    current: Comment,
    resolved: bool,
) -> None:
    comments.get.return_value = current
    result = await sut.execute(params(resolved))
    assert result.model_dump(exclude={"created_by_you"}) == current.model_dump(
        exclude={"created_by_you"}
    )
    comments.update_resolution.assert_not_awaited()
    notifier.notify_changed.assert_not_awaited()


async def test_should_tell_whether_the_caller_wrote_it(
    sut: UpdateCommentResolution, comments: AsyncMock
) -> None:
    anas = OPEN.model_copy(update={"author_id": ANA_ID})
    comments.get.return_value = anas
    assert (await sut.execute(params(True, ANA))).created_by_you is True
    comments.get.return_value = anas.model_copy(update={"resolved_at": datetime.now(UTC)})
    assert (await sut.execute(params(True, ANA))).created_by_you is True


async def test_should_report_comments_missing_from_the_diagram(
    sut: UpdateCommentResolution, comments: AsyncMock
) -> None:
    comments.get.return_value = None
    with pytest.raises(NotFoundError, match=f"^Comment {OPEN.id} not found in this diagram$"):
        await sut.execute(params(True))
    comments.update_resolution.assert_not_awaited()


@pytest.mark.parametrize(
    ("current", "resolved", "verb"), [(OPEN, True, "resolved"), (RESOLVED, False, "reopened")]
)
async def test_should_log_who_changed_it(
    sut: UpdateCommentResolution,
    comments: AsyncMock,
    caplog: pytest.LogCaptureFixture,
    current: Comment,
    resolved: bool,
    verb: str,
) -> None:
    comments.get.return_value = current
    with caplog.at_level(logging.INFO):
        await sut.execute(params(resolved))
    assert caplog.messages == [
        f"Comment {OPEN.id} on diagram {DIAGRAM_ID} {verb} by {ANAS_AGENT.audit_label}"
    ]
