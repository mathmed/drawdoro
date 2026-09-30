import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.gallery.delete_gallery_item import (
    DeleteGalleryItem,
    DeleteGalleryItemParams,
)

from .conftest import FOREIGN_ITEMS, OWNER_ID, make_item


@pytest.fixture
def sut(repo: GalleryItemRepository) -> DeleteGalleryItem:
    return DeleteGalleryItem(repo)


async def test_should_delete_owned_item(
    sut: DeleteGalleryItem, repo: GalleryItemRepository
) -> None:
    item = make_item()
    repo.get_by_id = AsyncMock(return_value=item)  # type: ignore[method-assign]
    repo.delete = AsyncMock()  # type: ignore[method-assign]

    await sut.execute(DeleteGalleryItemParams(item_id=item.id, owner_id=OWNER_ID))

    repo.delete.assert_awaited_once_with(item.id)


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_not_delete_items_of_other_owners(
    sut: DeleteGalleryItem, repo: GalleryItemRepository, stored: GalleryItem | None
) -> None:
    repo.get_by_id = AsyncMock(return_value=stored)  # type: ignore[method-assign]
    repo.delete = AsyncMock()  # type: ignore[method-assign]

    with pytest.raises(NotFoundError):
        await sut.execute(DeleteGalleryItemParams(item_id=uuid.uuid4(), owner_id=OWNER_ID))
    repo.delete.assert_not_awaited()
