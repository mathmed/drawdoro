import uuid

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.services.gallery_item_name import normalize_gallery_item_name
from app.domain.services.gallery_ownership import get_owned_gallery_item


class RenameGalleryItemParams(InputData):
    item_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    name: str


class RenameGalleryItem(Usecase[RenameGalleryItemParams, GalleryItemSummary]):
    def __init__(self, repo: GalleryItemRepository) -> None:
        self._repo = repo

    async def execute(self, params: RenameGalleryItemParams) -> GalleryItemSummary:
        name = normalize_gallery_item_name(params.name)
        await get_owned_gallery_item(self._repo, params.item_id, params.owner_id)
        return await self._repo.rename(params.item_id, name)
