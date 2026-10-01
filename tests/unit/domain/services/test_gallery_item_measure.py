from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.services.gallery_item_measure import (
    content_root_shapes,
    content_size_bytes,
    measure_gallery_item,
    measure_image,
    measure_shapes,
)
from tests.tldraw_records import content, geo, group, png


def test_should_measure_the_bounds_of_the_root_shapes() -> None:
    saved = content(
        [
            geo("shape:a", 100, 50, 80, 40),
            group("shape:g", 300, 10),
            geo("shape:b", 0, 0, 20, 300, parent="shape:g"),
        ]
    )
    measure = measure_shapes(saved)
    assert (measure.width, measure.height) == (220, 300)
    assert measure.size_bytes == content_size_bytes(saved)


def test_should_round_the_measured_size() -> None:
    measure = measure_shapes(content([geo("shape:a", 0, 0, 10.123, 5.456)]))
    assert (measure.width, measure.height) == (10.12, 5.46)


def test_should_leave_the_size_of_empty_content_unknown() -> None:
    measure = measure_shapes({"shapes": ["not a shape"]})
    assert (measure.width, measure.height) == (None, None)
    assert measure.size_bytes == len(b'{"shapes": ["not a shape"]}')


def test_should_find_roots_without_a_saved_list() -> None:
    shapes = [geo("shape:a"), geo("shape:b", parent="shape:a"), geo("shape:c", parent="shape:x")]
    assert [s["id"] for s in content_root_shapes({"shapes": shapes})] == ["shape:a", "shape:c"]
    listed = {"shapes": shapes, "rootShapeIds": ["shape:b"]}
    assert [s["id"] for s in content_root_shapes(listed)] == ["shape:b"]


def test_should_measure_images_from_their_header() -> None:
    data = png(64, 32)
    measure = measure_image(data, ImageMimeType.PNG)
    assert (measure.width, measure.height, measure.size_bytes) == (64, 32, len(data))
    unreadable = measure_image(b"\x89PNG\r\n\x1a\n", ImageMimeType.PNG)
    assert (unreadable.width, unreadable.height, unreadable.size_bytes) == (None, None, 8)


def test_should_measure_an_item_by_its_kind() -> None:
    image = GalleryItem(
        name="i",
        kind=GalleryItemKind.IMAGE,
        image_data=png(5, 6),
        image_mime_type=ImageMimeType.PNG,
    )
    shapes = GalleryItem(name="s", kind=GalleryItemKind.SHAPES, content=content([geo("shape:a")]))
    assert (measure_gallery_item(image).width, measure_gallery_item(image).height) == (5, 6)
    assert measure_gallery_item(shapes).width == 100
    assert measure_gallery_item(GalleryItem(name="x", kind=GalleryItemKind.SHAPES)).width is None
