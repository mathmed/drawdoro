from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.entities.objects.gallery_search import GallerySearch


def matches_gallery_search(item: GalleryItemSummary, search: GallerySearch) -> bool:
    return (
        _kind_matches(item, search) and _tag_matches(item, search) and _text_matches(item, search)
    )


def _kind_matches(item: GalleryItemSummary, search: GallerySearch) -> bool:
    return search.kind is None or item.kind == search.kind


def _tag_matches(item: GalleryItemSummary, search: GallerySearch) -> bool:
    tag = (search.tag or "").strip().lower()
    return tag == "" or tag in item.tags


def _text_matches(item: GalleryItemSummary, search: GallerySearch) -> bool:
    haystack = " ".join([item.name, item.description or "", *item.tags]).lower()
    return all(word in haystack for word in (search.text or "").lower().split())


def search_gallery_items(
    items: list[GalleryItemSummary], search: GallerySearch, limit: int | None = None
) -> list[GalleryItemSummary]:
    found = [item for item in items if matches_gallery_search(item, search)]
    return found if limit is None else found[:limit]
