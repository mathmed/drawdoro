from abc import ABC, abstractmethod

from app.domain.entities.models.comment import Comment


class CommentRepository(ABC):
    @abstractmethod
    def create(self, _comment: Comment) -> Comment: ...

    @abstractmethod
    def list_by_diagram(self, _diagram_id: str) -> list[Comment]: ...
