import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary


class GalleryItemRepository(ABC):
    @abstractmethod
    async def create(self, item: GalleryItem) -> GalleryItem: ...

    @abstractmethod
    async def get_by_id(self, item_id: uuid.UUID) -> GalleryItem | None: ...

    @abstractmethod
    async def list_by_owner(self, owner_id: uuid.UUID | None) -> list[GalleryItemSummary]: ...

    @abstractmethod
    async def rename(self, item_id: uuid.UUID, name: str) -> GalleryItemSummary: ...

    @abstractmethod
    async def delete(self, item_id: uuid.UUID) -> None: ...
