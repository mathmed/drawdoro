import uuid

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.entities.objects.gallery_search import GallerySearch
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.services.gallery_search import search_gallery_items


class ListGalleryItemsParams(InputData):
    owner_id: uuid.UUID | None = None
    # Words to find in the name, description and tags; all of them must match.
    query: str | None = None
    kind: GalleryItemKind | None = None
    tag: str | None = None
    limit: int | None = None
    include_thumbnails: bool = True


class ListGalleryItems(Usecase[ListGalleryItemsParams, list[GalleryItemSummary]]):
    def __init__(self, repo: GalleryItemRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListGalleryItemsParams) -> list[GalleryItemSummary]:
        items = await self._repo.list_by_owner(params.owner_id, params.include_thumbnails)
        search = GallerySearch(text=params.query, kind=params.kind, tag=params.tag)
        return search_gallery_items(items, search, params.limit)
