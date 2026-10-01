import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem, GetGalleryItemParams
from tests.tldraw_records import png

from .conftest import FOREIGN_ITEMS, OWNER_ID, make_item


@pytest.fixture
def sut(repo: GalleryItemRepository) -> GetGalleryItem:
    return GetGalleryItem(repo)


async def test_should_get_a_measured_item_as_stored(
    sut: GetGalleryItem, repo: GalleryItemRepository
) -> None:
    item = make_item().model_copy(update={"width": 1, "height": 2, "size_bytes": 3})
    repo.get_by_id = AsyncMock(return_value=item)  # type: ignore[method-assign]

    assert await sut.execute(GetGalleryItemParams(item_id=item.id, owner_id=OWNER_ID)) is item


@pytest.mark.parametrize(
    "measured", [{"width": None, "size_bytes": 3}, {"width": 1, "size_bytes": None}]
)
async def test_should_measure_items_saved_before_measures_existed(
    sut: GetGalleryItem, repo: GalleryItemRepository, measured: dict[str, object]
) -> None:
    data = png(30, 20)
    item = GalleryItem(
        owner_id=OWNER_ID,
        name="Logo",
        kind=GalleryItemKind.IMAGE,
        image_data=data,
        image_mime_type=ImageMimeType.PNG,
    ).model_copy(update=measured)
    repo.get_by_id = AsyncMock(return_value=item)  # type: ignore[method-assign]

    result = await sut.execute(GetGalleryItemParams(item_id=item.id, owner_id=OWNER_ID))

    assert (result.width, result.height, result.size_bytes) == (30, 20, len(data))
    assert result.image_data == data


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_raise_not_found_for_items_of_other_owners(
    sut: GetGalleryItem, repo: GalleryItemRepository, stored: GalleryItem | None
) -> None:
    repo.get_by_id = AsyncMock(return_value=stored)  # type: ignore[method-assign]
    item_id = uuid.uuid4()

    with pytest.raises(NotFoundError, match=str(item_id)):
        await sut.execute(GetGalleryItemParams(item_id=item_id, owner_id=OWNER_ID))
