import struct
from collections.abc import Callable

from app.domain.enums.image_mime_type import ImageMimeType

# JPEG start-of-frame markers, which carry the image size (C4, C8 and CC are other segments).
_JPEG_FRAME_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
# Markers without a length field after them.
_JPEG_STANDALONE_MARKERS = {0x01, *range(0xD0, 0xDA)}
# Little-endian WebP size fields: two 16-bit dimensions (lossy), one 32-bit bit field (lossless).
_WEBP_LOSSY_DIMENSIONS = struct.Struct("<HH")
_WEBP_LOSSLESS_BITS = struct.Struct("<I")


# Width and height in pixels, read from the file header; None when the header is unreadable.
def read_image_size(data: bytes, mime_type: ImageMimeType) -> tuple[int, int] | None:
    size = _READERS[mime_type](data)
    if size is None or min(size) <= 0:
        return None
    return size


def _png_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20]), int.from_bytes(data[20:24])


def _gif_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 10:
        return None
    return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    offset = 2
    while offset + 9 <= len(data) and data[offset] == 0xFF:
        marker = data[offset + 1]
        if marker in _JPEG_FRAME_MARKERS:
            height = int.from_bytes(data[offset + 5 : offset + 7])
            width = int.from_bytes(data[offset + 7 : offset + 9])
            return width, height
        offset = _next_jpeg_segment(data, offset, marker)
    return None


def _next_jpeg_segment(data: bytes, offset: int, marker: int) -> int:
    # 0xFF repeats are padding before a marker; standalone markers have no length.
    if marker == 0xFF:
        return offset + 1
    if marker in _JPEG_STANDALONE_MARKERS:
        return offset + 2
    return offset + 2 + int.from_bytes(data[offset + 2 : offset + 4])


def _webp_size(data: bytes) -> tuple[int, int] | None:
    flavour = _WEBP_READERS.get(data[12:16])
    if flavour is None or len(data) < flavour[1]:
        return None
    return flavour[0](data)


# The top two bits of each 16-bit lossy dimension are a scale hint, not part of the size.
def _webp_lossy_size(data: bytes) -> tuple[int, int]:
    width, height = _WEBP_LOSSY_DIMENSIONS.unpack_from(data, 26)
    return width & 0x3FFF, height & 0x3FFF


def _webp_lossless_size(data: bytes) -> tuple[int, int]:
    (bits,) = _WEBP_LOSSLESS_BITS.unpack_from(data, 21)
    return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1


def _webp_extended_size(data: bytes) -> tuple[int, int]:
    return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1


# Each WebP flavour keeps its size at a different place, so its header has a different length.
_WEBP_READERS: dict[bytes, tuple[Callable[[bytes], tuple[int, int]], int]] = {
    b"VP8 ": (_webp_lossy_size, 30),
    b"VP8L": (_webp_lossless_size, 25),
    b"VP8X": (_webp_extended_size, 30),
}
_READERS = {
    ImageMimeType.PNG: _png_size,
    ImageMimeType.GIF: _gif_size,
    ImageMimeType.JPEG: _jpeg_size,
    ImageMimeType.WEBP: _webp_size,
}
