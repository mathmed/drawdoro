import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError
from app.domain.usecases.gallery.rename_gallery_item import (
    RenameGalleryItem,
    RenameGalleryItemParams,
)

from .conftest import FOREIGN_ITEMS, OWNER_ID, make_item


@pytest.fixture
def sut(repo: GalleryItemRepository) -> RenameGalleryItem:
    return RenameGalleryItem(repo)


async def test_should_rename_owned_item_with_trimmed_name(
    sut: RenameGalleryItem, repo: GalleryItemRepository
) -> None:
    item = make_item()
    renamed = GalleryItemSummary(id=item.id, name="New", kind=GalleryItemKind.SHAPES)
    repo.get_by_id = AsyncMock(return_value=item)  # type: ignore[method-assign]
    repo.rename = AsyncMock(return_value=renamed)  # type: ignore[method-assign]

    result = await sut.execute(
        RenameGalleryItemParams(item_id=item.id, owner_id=OWNER_ID, name="  New ")
    )

    assert result is renamed
    repo.rename.assert_awaited_once_with(item.id, "New")


async def test_should_reject_blank_name(sut: RenameGalleryItem) -> None:
    with pytest.raises(InvalidInputError):
        await sut.execute(RenameGalleryItemParams(item_id=uuid.uuid4(), name=" "))


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_not_rename_items_of_other_owners(
    sut: RenameGalleryItem, repo: GalleryItemRepository, stored: GalleryItem | None
) -> None:
    repo.get_by_id = AsyncMock(return_value=stored)  # type: ignore[method-assign]
    repo.rename = AsyncMock()  # type: ignore[method-assign]

    with pytest.raises(NotFoundError):
        await sut.execute(
            RenameGalleryItemParams(item_id=uuid.uuid4(), owner_id=OWNER_ID, name="New")
        )
    repo.rename.assert_not_awaited()
