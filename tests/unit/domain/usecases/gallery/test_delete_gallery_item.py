import uuid
from unittest.mock import AsyncMock, NonCallableMagicMock

import pytest

from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.gallery.delete_gallery_item import (
    DeleteGalleryItem,
    DeleteGalleryItemParams,
)

from .conftest import FOREIGN_ITEMS, OWNER_ID, make_item


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> DeleteGalleryItem:
    return DeleteGalleryItem(repo)


async def test_should_delete_owned_item(sut: DeleteGalleryItem, repo: NonCallableMagicMock) -> None:
    item = make_item()
    repo.get_by_id.return_value = item
    repo.delete = AsyncMock()

    await sut.execute(DeleteGalleryItemParams(item_id=item.id, owner_id=OWNER_ID))

    repo.get_by_id.assert_awaited_once_with(item.id)
    repo.delete.assert_awaited_once_with(item.id)


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_not_delete_items_of_other_owners(
    sut: DeleteGalleryItem, repo: NonCallableMagicMock, stored: GalleryItem | None
) -> None:
    repo.get_by_id.return_value = stored
    repo.delete = AsyncMock()

    with pytest.raises(NotFoundError):
        await sut.execute(DeleteGalleryItemParams(item_id=uuid.uuid4(), owner_id=OWNER_ID))
    repo.delete.assert_not_awaited()
