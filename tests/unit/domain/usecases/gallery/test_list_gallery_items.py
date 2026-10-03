from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.usecases.gallery.list_gallery_items import (
    ListGalleryItems,
    ListGalleryItemsParams,
)

from .conftest import OWNER_ID

LOGO = GalleryItemSummary(
    owner_id=OWNER_ID, name="Temporal", kind=GalleryItemKind.IMAGE, tags=["workflow"]
)
CLUSTER = GalleryItemSummary(
    owner_id=OWNER_ID, name="Cluster", kind=GalleryItemKind.SHAPES, tags=["k8s"]
)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ListGalleryItems:
    repo.list_by_owner.return_value = [LOGO, CLUSTER]
    return ListGalleryItems(repo)


async def test_should_list_only_the_owner_items(
    sut: ListGalleryItems, repo: NonCallableMagicMock
) -> None:
    result = await sut.execute(ListGalleryItemsParams(owner_id=OWNER_ID))

    assert result == [LOGO, CLUSTER]
    repo.list_by_owner.assert_awaited_once_with(OWNER_ID, True)


async def test_should_leave_thumbnails_out_when_asked(
    sut: ListGalleryItems, repo: NonCallableMagicMock
) -> None:
    await sut.execute(ListGalleryItemsParams(owner_id=OWNER_ID, include_thumbnails=False))

    repo.list_by_owner.assert_awaited_once_with(OWNER_ID, False)


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        (ListGalleryItemsParams(query="temporal"), [LOGO]),
        (ListGalleryItemsParams(tag="K8S"), [CLUSTER]),
        (ListGalleryItemsParams(kind=GalleryItemKind.IMAGE), [LOGO]),
        (ListGalleryItemsParams(query="workflow", kind=GalleryItemKind.SHAPES), []),
        (ListGalleryItemsParams(limit=1), [LOGO]),
    ],
)
async def test_should_search_and_limit(
    sut: ListGalleryItems, params: ListGalleryItemsParams, expected: list[GalleryItemSummary]
) -> None:
    assert await sut.execute(params) == expected
