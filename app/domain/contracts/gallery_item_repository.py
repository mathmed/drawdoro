import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary


class GalleryItemRepository(ABC):
    @abstractmethod
    async def create(self, item: GalleryItem) -> GalleryItem: ...

    @abstractmethod
    async def get_by_id(self, item_id: uuid.UUID) -> GalleryItem | None: ...

    # Newest first. Thumbnails can be left out when the caller won't show them (e.g. agents).
    @abstractmethod
    async def list_by_owner(
        self, owner_id: uuid.UUID | None, include_thumbnails: bool = True
    ) -> list[GalleryItemSummary]: ...

    # Writes the name, tags and description of the item as given.
    @abstractmethod
    async def update_details(self, item: GalleryItemSummary) -> GalleryItemSummary: ...

    @abstractmethod
    async def delete(self, item_id: uuid.UUID) -> None: ...
