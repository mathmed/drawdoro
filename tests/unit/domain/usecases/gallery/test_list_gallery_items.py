from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.usecases.gallery.list_gallery_items import (
    ListGalleryItems,
    ListGalleryItemsParams,
)

from .conftest import OWNER_ID


@pytest.fixture
def sut(repo: GalleryItemRepository) -> ListGalleryItems:
    return ListGalleryItems(repo)


async def test_should_list_only_the_owner_items(
    sut: ListGalleryItems, repo: GalleryItemRepository
) -> None:
    summaries = [GalleryItemSummary(owner_id=OWNER_ID, name="a", kind=GalleryItemKind.IMAGE)]
    repo.list_by_owner = AsyncMock(return_value=summaries)  # type: ignore[method-assign]

    result = await sut.execute(ListGalleryItemsParams(owner_id=OWNER_ID))

    assert result == summaries
    repo.list_by_owner.assert_awaited_once_with(OWNER_ID)
