import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError
from app.domain.usecases.gallery.update_gallery_item import (
    UpdateGalleryItem,
    UpdateGalleryItemParams,
)

from .conftest import FOREIGN_ITEMS, OWNER_ID, make_item


@pytest.fixture
def item() -> GalleryItem:
    return make_item().model_copy(update={"tags": ["old"], "description": "Before"})


@pytest.fixture
def sut(repo: GalleryItemRepository, item: GalleryItem) -> UpdateGalleryItem:
    repo.get_by_id = AsyncMock(return_value=item)  # type: ignore[method-assign]
    repo.update_details = AsyncMock(side_effect=lambda summary: summary)  # type: ignore[method-assign]
    return UpdateGalleryItem(repo)


def saved(repo: GalleryItemRepository) -> GalleryItemSummary:
    summary: GalleryItemSummary = repo.update_details.await_args.args[0]  # type: ignore[attr-defined]
    return summary


async def test_should_rename_with_a_trimmed_name_and_keep_the_rest(
    sut: UpdateGalleryItem, repo: GalleryItemRepository, item: GalleryItem
) -> None:
    result = await sut.execute(
        UpdateGalleryItemParams(item_id=item.id, owner_id=OWNER_ID, name="  New ")
    )

    assert (result.name, result.tags, result.description) == ("New", ["old"], "Before")
    assert saved(repo).id == item.id
    assert not hasattr(saved(repo), "content")


# Ownership is checked on the item that was loaded, so it must be the one asked for.
async def test_should_load_the_requested_item(
    sut: UpdateGalleryItem, repo: GalleryItemRepository, item: GalleryItem
) -> None:
    await sut.execute(UpdateGalleryItemParams(item_id=item.id, owner_id=OWNER_ID, name="New"))

    repo.get_by_id.assert_awaited_once_with(item.id)  # type: ignore[attr-defined]


async def test_should_replace_tags_with_normalized_ones(
    sut: UpdateGalleryItem, repo: GalleryItemRepository, item: GalleryItem
) -> None:
    result = await sut.execute(
        UpdateGalleryItemParams(item_id=item.id, owner_id=OWNER_ID, tags=["AWS", " aws", "Queue"])
    )

    assert (result.name, result.tags, result.description) == ("Item", ["aws", "queue"], "Before")


async def test_should_clear_tags_and_description(sut: UpdateGalleryItem, item: GalleryItem) -> None:
    result = await sut.execute(
        UpdateGalleryItemParams(item_id=item.id, owner_id=OWNER_ID, tags=[], description="  ")
    )

    assert (result.tags, result.description) == ([], None)


async def test_should_set_the_description(sut: UpdateGalleryItem, item: GalleryItem) -> None:
    result = await sut.execute(
        UpdateGalleryItemParams(item_id=item.id, owner_id=OWNER_ID, description=" After ")
    )
    assert result.description == "After"


async def test_should_need_something_to_change(
    sut: UpdateGalleryItem, repo: GalleryItemRepository
) -> None:
    with pytest.raises(InvalidInputError) as refused:
        await sut.execute(UpdateGalleryItemParams(item_id=uuid.uuid4(), owner_id=OWNER_ID))
    assert refused.value.message == "Pass the name, tags or description to change"
    repo.get_by_id.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "params",
    [
        UpdateGalleryItemParams(item_id=uuid.uuid4(), name=" "),
        UpdateGalleryItemParams(item_id=uuid.uuid4(), tags=["a" * 40]),
        UpdateGalleryItemParams(item_id=uuid.uuid4(), description="a" * 501),
    ],
)
async def test_should_reject_invalid_values_before_reading(
    sut: UpdateGalleryItem, repo: GalleryItemRepository, params: UpdateGalleryItemParams
) -> None:
    with pytest.raises(InvalidInputError):
        await sut.execute(params)
    repo.get_by_id.assert_not_awaited()  # type: ignore[attr-defined]
    repo.update_details.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_not_update_items_of_other_owners(
    sut: UpdateGalleryItem, repo: GalleryItemRepository, stored: GalleryItem | None
) -> None:
    repo.get_by_id = AsyncMock(return_value=stored)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError):
        await sut.execute(
            UpdateGalleryItemParams(item_id=uuid.uuid4(), owner_id=OWNER_ID, name="New")
        )
    repo.update_details.assert_not_awaited()  # type: ignore[attr-defined]
