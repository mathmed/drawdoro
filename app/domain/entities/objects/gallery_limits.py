from dataclasses import dataclass


@dataclass(frozen=True)
class GalleryLimits:
    max_image_bytes: int
    max_shapes_bytes: int
    # Inserting an item fails when the diagram's canvas would grow beyond this.
    max_canvas_bytes: int = 20 * 1024 * 1024
