from app.domain.enums.image_mime_type import ImageMimeType

# The declared content type is never trusted: the type comes from the file signature, and only
# raster formats are accepted (SVG can carry scripts).
_SIGNATURES: list[tuple[bytes, ImageMimeType]] = [
    (b"\x89PNG\r\n\x1a\n", ImageMimeType.PNG),
    (b"\xff\xd8\xff", ImageMimeType.JPEG),
    (b"GIF87a", ImageMimeType.GIF),
    (b"GIF89a", ImageMimeType.GIF),
]


def detect_image_mime_type(data: bytes) -> ImageMimeType | None:
    for signature, mime_type in _SIGNATURES:
        if data.startswith(signature):
            return mime_type
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ImageMimeType.WEBP
    return None
