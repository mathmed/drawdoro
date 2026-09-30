from dataclasses import dataclass


@dataclass(frozen=True)
class GalleryLimits:
    max_image_bytes: int
    max_shapes_bytes: int
