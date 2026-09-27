import uuid

from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.comment import Comment


class CreateCommentParams(InputData):
    diagram_id: uuid.UUID
    element_id: str
    content: str
    author_id: uuid.UUID | None = None


class CreateComment(Usecase[CreateCommentParams, Comment]):
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateCommentParams) -> Comment:
        comment = Comment(
            diagram_id=params.diagram_id,
            element_id=params.element_id,
            content=params.content,
            author_id=params.author_id,
        )
        return await self._repo.create(comment)
