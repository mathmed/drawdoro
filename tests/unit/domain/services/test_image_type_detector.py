import pytest

from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.services.image_type_detector import detect_image_mime_type


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x89PNG\r\n\x1a\nrest", ImageMimeType.PNG),
        (b"\xff\xd8\xff\xe0rest", ImageMimeType.JPEG),
        (b"GIF87arest", ImageMimeType.GIF),
        (b"GIF89arest", ImageMimeType.GIF),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", ImageMimeType.WEBP),
    ],
)
def test_should_detect_supported_image_types(data: bytes, expected: ImageMimeType) -> None:
    assert detect_image_mime_type(data) == expected


@pytest.mark.parametrize(
    "data",
    [b"", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", b"RIFF\x00\x00\x00\x00WAVE", b"%PDF"],
)
def test_should_reject_unsupported_content(data: bytes) -> None:
    assert detect_image_mime_type(data) is None
