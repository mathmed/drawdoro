import json
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.constants.gallery import GALLERY_MAX_THUMBNAIL_BYTES
from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.errors.domain_errors import InvalidInputError, PayloadTooLargeError
from app.domain.usecases.gallery.create_gallery_item import (
    CreateGalleryItem,
    CreateGalleryItemParams,
)
from tests.tldraw_records import content, geo, png

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
CONTENT: dict[str, Any] = {"shapes": [{"id": "shape:a"}], "rootShapeIds": ["shape:a"]}


@pytest.fixture
def repo() -> GalleryItemRepository:
    mock = cast(GalleryItemRepository, create_autospec(GalleryItemRepository))
    mock.create = AsyncMock(side_effect=lambda item: item)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def sut(repo: GalleryItemRepository) -> CreateGalleryItem:
    return CreateGalleryItem(repo, GalleryLimits(max_image_bytes=64, max_shapes_bytes=200))


async def test_should_create_shapes_item_for_owner(sut: CreateGalleryItem) -> None:
    owner_id = uuid.uuid4()

    item = await sut.execute(
        CreateGalleryItemParams(
            owner_id=owner_id,
            name="  Load balancer  ",
            kind=GalleryItemKind.SHAPES,
            content=CONTENT,
            thumbnail=PNG,
        )
    )

    assert item.owner_id == owner_id
    assert item.name == "Load balancer"
    assert item.content == CONTENT
    assert item.thumbnail == PNG
    assert item.image_data is None


async def test_should_create_image_item_with_detected_mime_type(sut: CreateGalleryItem) -> None:
    item = await sut.execute(
        CreateGalleryItemParams(name="Logo", kind=GalleryItemKind.IMAGE, image_data=JPEG)
    )

    assert item.image_data == JPEG
    assert item.image_mime_type == ImageMimeType.JPEG
    assert item.content is None


NEEDS_CONTENT = "A shapes item needs content and no image"
NEEDS_SHAPES = "A shapes item needs at least one shape"
NEEDS_IMAGE = "An image item needs image data and no content"


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (CreateGalleryItemParams(name="x", kind=GalleryItemKind.SHAPES), NEEDS_CONTENT),
        (
            CreateGalleryItemParams(
                name="x", kind=GalleryItemKind.SHAPES, content=CONTENT, image_data=PNG
            ),
            NEEDS_CONTENT,
        ),
        (
            CreateGalleryItemParams(name="x", kind=GalleryItemKind.SHAPES, content={"shapes": []}),
            NEEDS_SHAPES,
        ),
        (
            CreateGalleryItemParams(name="x", kind=GalleryItemKind.SHAPES, content={"shapes": "a"}),
            NEEDS_SHAPES,
        ),
        (CreateGalleryItemParams(name="x", kind=GalleryItemKind.IMAGE), NEEDS_IMAGE),
        (
            CreateGalleryItemParams(
                name="x", kind=GalleryItemKind.IMAGE, image_data=PNG, content=CONTENT
            ),
            NEEDS_IMAGE,
        ),
        (
            CreateGalleryItemParams(
                name="x", kind=GalleryItemKind.IMAGE, image_data=b"<svg></svg>"
            ),
            "Unsupported image type: use PNG, JPEG, GIF or WebP",
        ),
        (
            CreateGalleryItemParams(name="   ", kind=GalleryItemKind.IMAGE, image_data=PNG),
            "Name must have 1 to 255 characters",
        ),
        (
            CreateGalleryItemParams(
                name="x", kind=GalleryItemKind.IMAGE, image_data=PNG, thumbnail=JPEG
            ),
            "The thumbnail must be a PNG image",
        ),
    ],
)
async def test_should_reject_invalid_input(
    sut: CreateGalleryItem,
    repo: GalleryItemRepository,
    params: CreateGalleryItemParams,
    message: str,
) -> None:
    with pytest.raises(InvalidInputError) as refused:
        await sut.execute(params)
    assert refused.value.message == message
    cast(AsyncMock, repo.create).assert_not_awaited()


# Saved content whose JSON takes exactly `size` bytes.
def sized_content(size: int) -> dict[str, Any]:
    empty = {"shapes": [{"id": "shape:a", "text": ""}]}
    padding = size - len(json.dumps(empty))
    return {"shapes": [{"id": "shape:a", "text": "a" * padding}]}


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (
            CreateGalleryItemParams(
                name="x", kind=GalleryItemKind.IMAGE, image_data=PNG + b"\x00" * 64
            ),
            "The image is too large (88 bytes, limit 64)",
        ),
        (
            CreateGalleryItemParams(
                name="x", kind=GalleryItemKind.SHAPES, content=sized_content(201)
            ),
            "The selection is too large (201 bytes, limit 200)",
        ),
        (
            CreateGalleryItemParams(
                name="x",
                kind=GalleryItemKind.IMAGE,
                image_data=PNG,
                thumbnail=PNG + b"\x00" * GALLERY_MAX_THUMBNAIL_BYTES,
            ),
            f"The thumbnail is too large (limit {GALLERY_MAX_THUMBNAIL_BYTES} bytes)",
        ),
    ],
)
async def test_should_reject_payloads_above_the_limit(
    sut: CreateGalleryItem, params: CreateGalleryItemParams, message: str
) -> None:
    with pytest.raises(PayloadTooLargeError) as refused:
        await sut.execute(params)
    assert refused.value.message == message


@pytest.mark.parametrize(
    "params",
    [
        CreateGalleryItemParams(
            name="x", kind=GalleryItemKind.IMAGE, image_data=PNG + b"\x00" * (64 - len(PNG))
        ),
        CreateGalleryItemParams(name="x", kind=GalleryItemKind.SHAPES, content=sized_content(200)),
        CreateGalleryItemParams(
            name="x",
            kind=GalleryItemKind.IMAGE,
            image_data=PNG,
            thumbnail=PNG + b"\x00" * (GALLERY_MAX_THUMBNAIL_BYTES - len(PNG)),
        ),
    ],
)
async def test_should_accept_payloads_exactly_at_the_limit(
    sut: CreateGalleryItem, repo: GalleryItemRepository, params: CreateGalleryItemParams
) -> None:
    await sut.execute(params)
    cast(AsyncMock, repo.create).assert_awaited_once()


async def test_should_return_what_the_repository_stored(
    sut: CreateGalleryItem, repo: GalleryItemRepository
) -> None:
    stored = GalleryItem(name="Stored", kind=GalleryItemKind.IMAGE, image_data=PNG)
    repo.create = AsyncMock(return_value=stored)  # type: ignore[method-assign]

    item = await sut.execute(
        CreateGalleryItemParams(name="x", kind=GalleryItemKind.IMAGE, image_data=PNG)
    )

    assert item is stored


async def test_should_normalize_tags_and_description(sut: CreateGalleryItem) -> None:
    item = await sut.execute(
        CreateGalleryItemParams(
            name="Logo",
            kind=GalleryItemKind.IMAGE,
            image_data=JPEG,
            tags=[" Kubernetes ", "K8S", "kubernetes"],
            description="  The wheel  ",
        )
    )

    assert item.tags == ["kubernetes", "k8s"]
    assert item.description == "The wheel"


async def test_should_reject_invalid_tags(
    sut: CreateGalleryItem, repo: GalleryItemRepository
) -> None:
    with pytest.raises(InvalidInputError, match="unsupported characters"):
        await sut.execute(
            CreateGalleryItemParams(
                name="Logo", kind=GalleryItemKind.IMAGE, image_data=JPEG, tags=["<b>"]
            )
        )
    repo.create.assert_not_called()  # type: ignore[attr-defined]


async def test_should_measure_images(repo: GalleryItemRepository) -> None:
    data = png(40, 30)
    sut = CreateGalleryItem(repo, GalleryLimits(max_image_bytes=10_000, max_shapes_bytes=200))

    item = await sut.execute(
        CreateGalleryItemParams(name="Logo", kind=GalleryItemKind.IMAGE, image_data=data)
    )

    assert (item.width, item.height, item.size_bytes) == (40, 30, len(data))


async def test_should_measure_shapes(repo: GalleryItemRepository) -> None:
    saved = content([geo("shape:a", 10, 10, 120, 60)])
    sut = CreateGalleryItem(repo, GalleryLimits(max_image_bytes=64, max_shapes_bytes=10_000))

    item = await sut.execute(
        CreateGalleryItemParams(name="Box", kind=GalleryItemKind.SHAPES, content=saved)
    )

    assert (item.width, item.height) == (120, 60)
    assert item.size_bytes == len(json.dumps(saved).encode())
