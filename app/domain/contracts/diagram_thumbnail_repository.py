import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.thumbnail_theme import ThumbnailTheme


class DiagramThumbnailRepository(ABC):
    # The images of a project's live diagrams in one theme, in a single query; diagrams without an
    # image are left out.
    @abstractmethod
    async def list_by_project(
        self, project_id: uuid.UUID, theme: ThumbnailTheme
    ) -> list[DiagramThumbnail]: ...

    # Stores each thumbnail unless one with a newer version is already there, atomically, so late,
    # retried or concurrent uploads never bring an older preview back.
    @abstractmethod
    async def save(self, thumbnails: list[DiagramThumbnail]) -> None: ...
