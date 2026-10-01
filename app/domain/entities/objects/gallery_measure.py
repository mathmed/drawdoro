from dataclasses import dataclass


@dataclass(frozen=True)
class GalleryMeasure:
    width: float | None
    height: float | None
    size_bytes: int
