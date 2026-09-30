import uuid

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.services.gallery_ownership import get_owned_gallery_item


class DeleteGalleryItemParams(InputData):
    item_id: uuid.UUID
    owner_id: uuid.UUID | None = None


class DeleteGalleryItem(Usecase[DeleteGalleryItemParams, None]):
    def __init__(self, repo: GalleryItemRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteGalleryItemParams) -> None:
        await get_owned_gallery_item(self._repo, params.item_id, params.owner_id)
        await self._repo.delete(params.item_id)
