import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.comment import Comment
from app.domain.enums.comment_status import CommentStatus


class CommentRepository(ABC):
    @abstractmethod
    async def create(self, comment: Comment) -> Comment: ...

    @abstractmethod
    async def list_by_diagram(
        self, diagram_id: uuid.UUID, status: CommentStatus = CommentStatus.ALL
    ) -> list[Comment]: ...

    # None when the comment doesn't exist or belongs to another diagram.
    @abstractmethod
    async def get(self, diagram_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None: ...

    @abstractmethod
    async def update_resolution(self, comment: Comment) -> Comment: ...

    @abstractmethod
    async def delete(self, comment_id: uuid.UUID) -> None: ...
