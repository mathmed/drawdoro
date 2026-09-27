import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.comment import Comment


class CommentRepository(ABC):
    @abstractmethod
    async def create(self, comment: Comment) -> Comment: ...

    @abstractmethod
    async def list_by_diagram(self, diagram_id: uuid.UUID) -> list[Comment]: ...

    @abstractmethod
    async def delete(self, comment_id: uuid.UUID) -> None: ...
