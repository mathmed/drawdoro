import logging
import uuid
from datetime import UTC, datetime

from app.domain.contracts.comment_change_notifier import CommentChangeNotifier
from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.comment_ownership import is_created_by

logger = logging.getLogger(__name__)


class UpdateCommentResolutionParams(InputData):
    diagram_id: uuid.UUID
    comment_id: uuid.UUID
    resolved: bool
    actor: CommentActor = CommentActor()


# Resolves or reopens a comment of any author: it's reversible, and who resolved it is kept, so
# people can review what agents closed. Repeating the current state changes nothing, so the first
# resolver stays on record.
class UpdateCommentResolution(Usecase[UpdateCommentResolutionParams, Comment]):
    def __init__(self, comments: CommentRepository, notifier: CommentChangeNotifier) -> None:
        self._comments = comments
        self._notifier = notifier

    async def execute(self, params: UpdateCommentResolutionParams) -> Comment:
        comment = await self._comments.get(params.diagram_id, params.comment_id)
        if comment is None:
            raise NotFoundError(f"Comment {params.comment_id} not found in this diagram")
        if comment.is_resolved == params.resolved:
            return _as_seen_by(comment, params.actor)
        changed = comment.model_copy(update=_resolution(params.resolved, params.actor))
        updated = await self._comments.update_resolution(changed)
        await self._notifier.notify_changed(params.diagram_id)
        logger.info(
            "Comment %s on diagram %s %s by %s",
            comment.id,
            params.diagram_id,
            "resolved" if params.resolved else "reopened",
            params.actor.audit_label,
        )
        return _as_seen_by(updated, params.actor)


def _resolution(resolved: bool, actor: CommentActor) -> dict[str, object]:
    if not resolved:
        return {
            "resolved_at": None,
            "resolved_by_id": None,
            "resolved_by_name": None,
            "resolved_by_origin": None,
            "resolved_by_agent_name": None,
            "resolved_by_agent_label": None,
        }
    return {
        "resolved_at": datetime.now(UTC),
        "resolved_by_id": actor.user_id,
        "resolved_by_origin": actor.origin,
        "resolved_by_agent_name": actor.agent_name,
        "resolved_by_agent_label": actor.agent_label,
    }


def _as_seen_by(comment: Comment, actor: CommentActor) -> Comment:
    return comment.model_copy(update={"created_by_you": is_created_by(comment, actor)})
