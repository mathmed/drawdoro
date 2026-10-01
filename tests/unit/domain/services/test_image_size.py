import struct

import pytest

from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.services.image_size import read_image_size
from tests.tldraw_records import png


def gif(width: int, height: int) -> bytes:
    return b"GIF89a" + struct.pack("<HH", width, height) + b"\x00" * 4


def jpeg(width: int, height: int) -> bytes:
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
    standalone = b"\xff\xff\xff\xd0"
    frame = b"\xff\xc2" + struct.pack(">HBHH", 17, 8, height, width) + b"\x00" * 10
    return b"\xff\xd8" + app0 + standalone + frame


def webp(chunk: bytes, payload: bytes) -> bytes:
    return b"RIFF" + b"\x00" * 4 + b"WEBP" + chunk + b"\x00" * 4 + payload


def test_should_read_png_size() -> None:
    assert read_image_size(png(640, 480), ImageMimeType.PNG) == (640, 480)


def test_should_read_gif_size() -> None:
    assert read_image_size(gif(300, 200), ImageMimeType.GIF) == (300, 200)


def test_should_read_jpeg_size_after_other_segments() -> None:
    assert read_image_size(jpeg(1024, 768), ImageMimeType.JPEG) == (1024, 768)


def test_should_read_lossy_webp_size() -> None:
    payload = b"\x00" * 6 + struct.pack("<HH", 0xC000 | 800, 600)
    assert read_image_size(webp(b"VP8 ", payload), ImageMimeType.WEBP) == (800, 600)


def test_should_read_lossless_webp_size() -> None:
    bits = (120 - 1) | ((90 - 1) << 14)
    payload = b"\x2f" + struct.pack("<I", bits)
    assert read_image_size(webp(b"VP8L", payload), ImageMimeType.WEBP) == (120, 90)


def test_should_read_extended_webp_size() -> None:
    payload = b"\x00" * 4 + (2000 - 1).to_bytes(3, "little") + (1000 - 1).to_bytes(3, "little")
    assert read_image_size(webp(b"VP8X", payload), ImageMimeType.WEBP) == (2000, 1000)


@pytest.mark.parametrize(
    ("data", "mime_type"),
    [
        (b"\x89PNG\r\n\x1a\n", ImageMimeType.PNG),
        (png(10, 10)[:20], ImageMimeType.PNG),
        (b"\x89PNG\r\n\x1a\n" + b"\x00" * 4 + b"XXXX" + b"\x00" * 8, ImageMimeType.PNG),
        (png(0, 10), ImageMimeType.PNG),
        (b"GIF89a\x01", ImageMimeType.GIF),
        (b"\xff\xd8\xff\xe0", ImageMimeType.JPEG),
        (b"\xff\xd8" + b"\x00" * 12, ImageMimeType.JPEG),
        (b"\xff\xd8" + b"\xff\xe0\x00\x02" + b"\x00" * 10, ImageMimeType.JPEG),
        (webp(b"VP8 ", b"\x00" * 2), ImageMimeType.WEBP),
        (webp(b"VP8L", b"\x00"), ImageMimeType.WEBP),
        (webp(b"VP8X", b"\x00" * 2), ImageMimeType.WEBP),
        (webp(b"ABCD", b"\x00" * 20), ImageMimeType.WEBP),
    ],
)
def test_should_return_none_for_unreadable_headers(data: bytes, mime_type: ImageMimeType) -> None:
    assert read_image_size(data, mime_type) is None
