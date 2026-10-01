import logging
import uuid

from app.domain.contracts.comment_change_notifier import CommentChangeNotifier
from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.services.comment_ownership import is_created_by

logger = logging.getLogger(__name__)


class DeleteCommentParams(InputData):
    diagram_id: uuid.UUID
    comment_id: uuid.UUID
    actor: CommentActor = CommentActor()


# People with write access delete any comment, as in the editor. Agents only delete what their
# own key wrote, so text planted in a comment can't get an agent to erase other people's comments.
class DeleteComment(Usecase[DeleteCommentParams, None]):
    def __init__(self, comments: CommentRepository, notifier: CommentChangeNotifier) -> None:
        self._comments = comments
        self._notifier = notifier

    async def execute(self, params: DeleteCommentParams) -> None:
        comment = await self._comments.get(params.diagram_id, params.comment_id)
        if comment is None:
            raise NotFoundError(f"Comment {params.comment_id} not found in this diagram")
        if params.actor.is_agent and not is_created_by(comment, params.actor):
            raise ForbiddenError(
                "Agents can only delete comments written with their own API key. "
                "Resolve this comment instead, or ask a person to delete it"
            )
        await self._comments.delete(comment.id)
        await self._notifier.notify_changed(params.diagram_id)
        logger.info(
            "Comment %s deleted from diagram %s by %s",
            comment.id,
            params.diagram_id,
            params.actor.audit_label,
        )
