import uuid

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.gallery_item import GalleryItemSummary


class ListGalleryItemsParams(InputData):
    owner_id: uuid.UUID | None = None


class ListGalleryItems(Usecase[ListGalleryItemsParams, list[GalleryItemSummary]]):
    def __init__(self, repo: GalleryItemRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListGalleryItemsParams) -> list[GalleryItemSummary]:
        return await self._repo.list_by_owner(params.owner_id)
