import uuid

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.errors.domain_errors import NotFoundError


async def get_owned_gallery_item(
    repo: GalleryItemRepository, item_id: uuid.UUID, owner_id: uuid.UUID | None
) -> GalleryItem:
    item = await repo.get_by_id(item_id)
    # Someone else's item answers exactly like a missing one, so ids cannot be probed.
    if item is None or item.owner_id != owner_id:
        raise NotFoundError(f"Gallery item {item_id} not found")
    return item
