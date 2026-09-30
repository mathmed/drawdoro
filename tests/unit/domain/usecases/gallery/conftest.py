import uuid
from typing import cast
from unittest.mock import create_autospec

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.enums.gallery_item_kind import GalleryItemKind

OWNER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def make_item(owner_id: uuid.UUID | None = OWNER_ID) -> GalleryItem:
    return GalleryItem(
        owner_id=owner_id, name="Item", kind=GalleryItemKind.SHAPES, content={"shapes": [{}]}
    )


# Items that the owner must not see: missing, someone else's, and ownerless (auth disabled).
FOREIGN_ITEMS = [None, make_item(owner_id=uuid.uuid4()), make_item(owner_id=None)]


@pytest.fixture
def repo() -> GalleryItemRepository:
    return cast(GalleryItemRepository, create_autospec(GalleryItemRepository))
