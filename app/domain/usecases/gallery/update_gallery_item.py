import uuid

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.errors.domain_errors import InvalidInputError
from app.domain.services.gallery_item_labels import (
    normalize_gallery_item_description,
    normalize_gallery_item_tags,
)
from app.domain.services.gallery_item_name import normalize_gallery_item_name
from app.domain.services.gallery_ownership import get_owned_gallery_item


class UpdateGalleryItemParams(InputData):
    item_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    # None leaves a field as it is; an empty description or tag list clears it.
    name: str | None = None
    tags: list[str] | None = None
    description: str | None = None


class UpdateGalleryItem(Usecase[UpdateGalleryItemParams, GalleryItemSummary]):
    def __init__(self, repo: GalleryItemRepository) -> None:
        self._repo = repo

    async def execute(self, params: UpdateGalleryItemParams) -> GalleryItemSummary:
        if params.name is None and params.tags is None and params.description is None:
            raise InvalidInputError("Pass the name, tags or description to change")
        changes: dict[str, object] = {}
        if params.name is not None:
            changes["name"] = normalize_gallery_item_name(params.name)
        if params.tags is not None:
            changes["tags"] = normalize_gallery_item_tags(params.tags)
        if params.description is not None:
            changes["description"] = normalize_gallery_item_description(params.description)
        item = await get_owned_gallery_item(self._repo, params.item_id, params.owner_id)
        summary = GalleryItemSummary.model_validate(
            item.model_dump(exclude={"content", "image_data"})
        )
        return await self._repo.update_details(summary.model_copy(update=changes))
