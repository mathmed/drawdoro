import logging
import uuid

from app.domain.contracts.comment_change_notifier import CommentChangeNotifier
from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.comment_content import normalize_comment_content, normalize_element_id

logger = logging.getLogger(__name__)


class CreateCommentParams(InputData):
    diagram_id: uuid.UUID
    content: str
    element_id: str | None = None
    actor: CommentActor = CommentActor()
    # Author named by the client; only honoured for people without a session (auth disabled).
    author_id: uuid.UUID | None = None


class CreateComment(Usecase[CreateCommentParams, Comment]):
    def __init__(
        self,
        comments: CommentRepository,
        diagrams: DiagramRepository,
        notifier: CommentChangeNotifier,
    ) -> None:
        self._comments = comments
        self._diagrams = diagrams
        self._notifier = notifier

    async def execute(self, params: CreateCommentParams) -> Comment:
        content = normalize_comment_content(params.content)
        element_id = normalize_element_id(params.element_id)
        if not await self._diagrams.exists(params.diagram_id):
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        actor = params.actor
        created = await self._comments.create(
            Comment(
                diagram_id=params.diagram_id,
                element_id=element_id,
                content=content,
                author_id=_author_id(params),
                origin=actor.origin,
                agent_name=actor.agent_name,
                agent_label=actor.agent_label,
                api_key_id=actor.api_key_id,
            )
        )
        await self._notifier.notify_changed(params.diagram_id)
        logger.info(
            "Comment %s created on diagram %s by %s",
            created.id,
            params.diagram_id,
            actor.audit_label,
        )
        return created.model_copy(update={"created_by_you": True})


# Agents and signed-in people are always the author; nobody can write in someone else's name.
def _author_id(params: CreateCommentParams) -> uuid.UUID | None:
    if params.actor.is_agent or params.actor.user_id is not None:
        return params.actor.user_id
    return params.author_id
