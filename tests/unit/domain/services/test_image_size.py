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


# Signature, IHDR length and type, width and height: the 24 bytes the reader needs, no pixels.
def png_header(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)
    )


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


def test_should_read_the_smallest_image() -> None:
    assert read_image_size(png(1, 1), ImageMimeType.PNG) == (1, 1)


def test_should_read_a_png_header_without_the_rest_of_the_file() -> None:
    assert read_image_size(png(640, 480)[:24], ImageMimeType.PNG) == (640, 480)


def test_should_read_every_byte_of_large_png_sizes() -> None:
    data = png_header(0x01020304, 0x05060708)
    assert len(data) == 24
    assert read_image_size(data, ImageMimeType.PNG) == (0x01020304, 0x05060708)


def test_should_read_a_gif_header_without_the_rest_of_the_file() -> None:
    assert read_image_size(gif(300, 200)[:10], ImageMimeType.GIF) == (300, 200)


def test_should_read_gif_size_before_the_screen_flags() -> None:
    data = b"GIF89a" + struct.pack("<HH", 300, 200) + b"\xf7\x00\x00"
    assert read_image_size(data, ImageMimeType.GIF) == (300, 200)


def test_should_read_a_jpeg_frame_that_ends_the_data() -> None:
    frame = b"\xff\xc0" + struct.pack(">HBHH", 17, 8, 768, 1024)
    assert read_image_size(b"\xff\xd8" + frame, ImageMimeType.JPEG) == (1024, 768)


def test_should_skip_any_number_of_jpeg_padding_bytes() -> None:
    frame = b"\xff\xc0" + struct.pack(">HBHH", 17, 8, 768, 1024) + b"\x00" * 10
    data = b"\xff\xd8" + b"\xff" * 3 + frame[1:]
    assert read_image_size(data, ImageMimeType.JPEG) == (1024, 768)


@pytest.mark.parametrize("payload_length", [0, 1, 300])
def test_should_skip_jpeg_segments_of_any_length(payload_length: int) -> None:
    segment = b"\xff\xe1" + struct.pack(">H", payload_length + 2) + b"\x00" * payload_length
    frame = b"\xff\xc0" + struct.pack(">HBHH", 17, 8, 768, 1024) + b"\x00" * 10
    assert read_image_size(b"\xff\xd8" + segment + frame, ImageMimeType.JPEG) == (1024, 768)


def test_should_read_extended_webp_size_before_the_next_chunk() -> None:
    size = (2000 - 1).to_bytes(3, "little") + (1000 - 1).to_bytes(3, "little")
    payload = b"\x00" * 4 + size + b"ICCP"
    assert read_image_size(webp(b"VP8X", payload), ImageMimeType.WEBP) == (2000, 1000)


@pytest.mark.parametrize(
    ("data", "mime_type"),
    [
        (b"\x89PNG\r\n\x1a\n", ImageMimeType.PNG),
        (png(10, 10)[:20], ImageMimeType.PNG),
        (b"\x89PNG\r\n\x1a\n" + b"\x00" * 4 + b"XXXX" + b"\x01" * 8, ImageMimeType.PNG),
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
