import uuid

from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.comment import Comment


class ListCommentsParams(InputData):
    diagram_id: uuid.UUID


class ListComments(Usecase[ListCommentsParams, list[Comment]]):
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListCommentsParams) -> list[Comment]:
        return await self._repo.list_by_diagram(params.diagram_id)
