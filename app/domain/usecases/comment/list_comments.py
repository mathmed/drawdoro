import uuid

from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.comment_status import CommentStatus
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.comment_ownership import is_created_by


class ListCommentsParams(InputData):
    diagram_id: uuid.UUID
    status: CommentStatus = CommentStatus.ALL
    actor: CommentActor = CommentActor()


class ListComments(Usecase[ListCommentsParams, list[Comment]]):
    def __init__(self, comments: CommentRepository, diagrams: DiagramRepository) -> None:
        self._comments = comments
        self._diagrams = diagrams

    async def execute(self, params: ListCommentsParams) -> list[Comment]:
        if not await self._diagrams.exists(params.diagram_id):
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        comments = await self._comments.list_by_diagram(params.diagram_id, params.status)
        return [
            comment.model_copy(update={"created_by_you": is_created_by(comment, params.actor)})
            for comment in comments
        ]
