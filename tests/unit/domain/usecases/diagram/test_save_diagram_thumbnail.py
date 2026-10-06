import uuid
from datetime import UTC, datetime
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.constants.thumbnails import DIAGRAM_THUMBNAIL_MAX_BYTES
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_thumbnail_repository import DiagramThumbnailRepository
from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.thumbnail_theme import ThumbnailTheme
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError, PayloadTooLargeError
from app.domain.usecases.diagram.save_diagram_thumbnail import (
    SaveDiagramThumbnail,
    SaveDiagramThumbnailParams,
)
from tests.doubles import double

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 16
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
VERSION = datetime(2026, 10, 6, 12, 30, tzinfo=UTC)
DIAGRAM_ID = uuid.uuid4()


@pytest.fixture
def diagrams() -> NonCallableMagicMock:
    mock = double(DiagramRepository)
    mock.exists.return_value = True
    return mock


@pytest.fixture
def thumbnails() -> NonCallableMagicMock:
    return double(DiagramThumbnailRepository)


@pytest.fixture
def sut(diagrams: NonCallableMagicMock, thumbnails: NonCallableMagicMock) -> SaveDiagramThumbnail:
    return SaveDiagramThumbnail(diagrams, thumbnails)


def saved(thumbnails: NonCallableMagicMock) -> list[DiagramThumbnail]:
    result: list[DiagramThumbnail] = thumbnails.save.await_args.args[0]
    return result


async def test_should_store_both_themes_with_their_detected_types_and_version(
    sut: SaveDiagramThumbnail, diagrams: NonCallableMagicMock, thumbnails: NonCallableMagicMock
) -> None:
    await sut.execute(
        SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION, light=PNG, dark=WEBP)
    )

    diagrams.exists.assert_awaited_once_with(DIAGRAM_ID)
    thumbnails.save.assert_awaited_once()
    assert saved(thumbnails) == [
        DiagramThumbnail(
            diagram_id=DIAGRAM_ID,
            theme=ThumbnailTheme.LIGHT,
            version=VERSION,
            image=PNG,
            mime_type=ImageMimeType.PNG,
        ),
        DiagramThumbnail(
            diagram_id=DIAGRAM_ID,
            theme=ThumbnailTheme.DARK,
            version=VERSION,
            image=WEBP,
            mime_type=ImageMimeType.WEBP,
        ),
    ]


async def test_should_clear_both_themes_when_the_diagram_has_nothing_to_draw(
    sut: SaveDiagramThumbnail, thumbnails: NonCallableMagicMock
) -> None:
    await sut.execute(SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION))

    assert saved(thumbnails) == [
        DiagramThumbnail(diagram_id=DIAGRAM_ID, theme=ThumbnailTheme.LIGHT, version=VERSION),
        DiagramThumbnail(diagram_id=DIAGRAM_ID, theme=ThumbnailTheme.DARK, version=VERSION),
    ]


async def test_should_store_one_theme_when_only_one_was_rendered(
    sut: SaveDiagramThumbnail, thumbnails: NonCallableMagicMock
) -> None:
    await sut.execute(SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION, dark=PNG))

    light, dark = saved(thumbnails)
    assert (light.image, light.mime_type) == (None, None)
    assert (dark.image, dark.mime_type) == (PNG, ImageMimeType.PNG)


async def test_should_accept_a_thumbnail_exactly_at_the_size_limit(
    sut: SaveDiagramThumbnail, thumbnails: NonCallableMagicMock
) -> None:
    image = PNG + b"\x00" * (DIAGRAM_THUMBNAIL_MAX_BYTES - len(PNG))

    await sut.execute(
        SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION, light=image)
    )

    assert saved(thumbnails)[0].image == image


@pytest.mark.parametrize("theme", ["light", "dark"])
async def test_should_reject_a_thumbnail_over_the_size_limit(
    sut: SaveDiagramThumbnail, thumbnails: NonCallableMagicMock, theme: str
) -> None:
    image = PNG + b"\x00" * (DIAGRAM_THUMBNAIL_MAX_BYTES - len(PNG) + 1)

    with pytest.raises(
        PayloadTooLargeError,
        match=rf"^The {theme} thumbnail is too large \(limit {DIAGRAM_THUMBNAIL_MAX_BYTES} bytes\)$",
    ):
        await sut.execute(
            SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION, **{theme: image})
        )
    thumbnails.save.assert_not_awaited()


@pytest.mark.parametrize("image", [JPEG, b"<svg xmlns='http://www.w3.org/2000/svg'/>", b""])
async def test_should_reject_a_thumbnail_that_is_not_png_or_webp(
    sut: SaveDiagramThumbnail, thumbnails: NonCallableMagicMock, image: bytes
) -> None:
    with pytest.raises(
        InvalidInputError, match=r"^The dark thumbnail must be a PNG or WebP image$"
    ):
        await sut.execute(
            SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION, dark=image)
        )
    thumbnails.save.assert_not_awaited()


async def test_should_raise_not_found_and_store_nothing_when_the_diagram_is_gone(
    sut: SaveDiagramThumbnail, diagrams: NonCallableMagicMock, thumbnails: NonCallableMagicMock
) -> None:
    diagrams.exists.return_value = False

    with pytest.raises(NotFoundError, match=rf"^Diagram {DIAGRAM_ID} not found$"):
        await sut.execute(
            SaveDiagramThumbnailParams(diagram_id=DIAGRAM_ID, version=VERSION, light=PNG)
        )
    thumbnails.save.assert_not_awaited()
