import json
from typing import Any

from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.entities.objects.gallery_measure import GalleryMeasure
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.services.canvas_geometry import (
    CanvasRecord,
    children_by_parent,
    shape_bounds,
    union_bounds,
)
from app.domain.services.image_size import read_image_size


def content_size_bytes(content: dict[str, Any]) -> int:
    return len(json.dumps(content).encode())


def saved_shapes(content: dict[str, Any]) -> list[CanvasRecord]:
    shapes = content.get("shapes")
    if not isinstance(shapes, list):
        return []
    return [shape for shape in shapes if isinstance(shape, dict)]


# The top-level shapes of saved content: the listed roots, or the shapes without a saved parent.
def content_root_shapes(content: dict[str, Any]) -> list[CanvasRecord]:
    shapes = saved_shapes(content)
    listed = content.get("rootShapeIds")
    if isinstance(listed, list) and listed:
        return [shape for shape in shapes if shape.get("id") in listed]
    ids = {shape.get("id") for shape in shapes}
    return [shape for shape in shapes if shape.get("parentId") not in ids]


def measure_shapes(content: dict[str, Any]) -> GalleryMeasure:
    children = children_by_parent(saved_shapes(content))
    bounds = union_bounds(shape_bounds(root, children) for root in content_root_shapes(content))
    size = content_size_bytes(content)
    if bounds is None:
        return GalleryMeasure(width=None, height=None, size_bytes=size)
    return GalleryMeasure(
        width=round(bounds.width, 2), height=round(bounds.height, 2), size_bytes=size
    )


def measure_image(data: bytes, mime_type: ImageMimeType) -> GalleryMeasure:
    size = read_image_size(data, mime_type)
    if size is None:
        return GalleryMeasure(width=None, height=None, size_bytes=len(data))
    return GalleryMeasure(width=size[0], height=size[1], size_bytes=len(data))


def measure_gallery_item(item: GalleryItem) -> GalleryMeasure:
    if item.image_data is not None and item.image_mime_type is not None:
        return measure_image(item.image_data, item.image_mime_type)
    return measure_shapes(item.content or {})
