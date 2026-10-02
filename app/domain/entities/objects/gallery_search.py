from dataclasses import dataclass

from app.domain.enums.gallery_item_kind import GalleryItemKind


# Every word of `text` must appear in the name, the description or a tag; `tag` must be one of
# the item's tags exactly. Both are compared in lower case.
@dataclass(frozen=True)
class GallerySearch:
    text: str | None = None
    kind: GalleryItemKind | None = None
    tag: str | None = None
