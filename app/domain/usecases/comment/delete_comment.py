import uuid

from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.usecase import InputData, Usecase


class DeleteCommentParams(InputData):
    comment_id: uuid.UUID


class DeleteComment(Usecase[DeleteCommentParams, None]):
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteCommentParams) -> None:
        await self._repo.delete(params.comment_id)
