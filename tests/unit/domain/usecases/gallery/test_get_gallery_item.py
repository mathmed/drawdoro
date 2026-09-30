import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem, GetGalleryItemParams

from .conftest import FOREIGN_ITEMS, OWNER_ID, make_item


@pytest.fixture
def sut(repo: GalleryItemRepository) -> GetGalleryItem:
    return GetGalleryItem(repo)


async def test_should_get_owned_item(sut: GetGalleryItem, repo: GalleryItemRepository) -> None:
    item = make_item()
    repo.get_by_id = AsyncMock(return_value=item)  # type: ignore[method-assign]

    assert await sut.execute(GetGalleryItemParams(item_id=item.id, owner_id=OWNER_ID)) is item


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_raise_not_found_for_items_of_other_owners(
    sut: GetGalleryItem, repo: GalleryItemRepository, stored: GalleryItem | None
) -> None:
    repo.get_by_id = AsyncMock(return_value=stored)  # type: ignore[method-assign]
    item_id = uuid.uuid4()

    with pytest.raises(NotFoundError, match=str(item_id)):
        await sut.execute(GetGalleryItemParams(item_id=item_id, owner_id=OWNER_ID))
