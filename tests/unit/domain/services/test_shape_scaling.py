from app.domain.services.shape_scaling import scale_shape
from tests.tldraw_records import arrow, geo, shape


def test_should_leave_shapes_alone_at_scale_one() -> None:
    record = geo("shape:a", w=10, h=20)
    scale_shape(record, 1)
    assert record == geo("shape:a", w=10, h=20)


def test_should_scale_size_stroke_and_custom_label_size() -> None:
    record = geo("shape:a", w=10, h=20)
    record["meta"] = {"fontSize": 18, "edges": "round"}
    scale_shape(record, 2)
    assert (record["props"]["w"], record["props"]["h"], record["props"]["scale"]) == (20, 40, 2)
    assert record["meta"] == {"fontSize": 36, "edges": "round"}


def test_should_scale_notes_and_text_only_through_their_scale() -> None:
    note = shape("shape:n", "note", scale=1)
    text = shape("shape:t", "text", w=100, scale=1.5)
    scale_shape(note, 3)
    scale_shape(text, 2)
    assert note["props"] == {"scale": 3}
    assert text["props"] == {"w": 100, "scale": 3}


def test_should_scale_arrow_ends_and_bend() -> None:
    record = arrow("shape:a", 0, 0, (100, 50))
    record["props"]["bend"] = 10
    scale_shape(record, 0.5)
    assert record["props"]["start"] == {"x": 0, "y": 0}
    assert record["props"]["end"] == {"x": 50, "y": 25}
    assert (record["props"]["bend"], record["props"]["scale"]) == (5, 0.5)


def test_should_scale_line_points_and_drawing_segments() -> None:
    line = shape("shape:l", "line", points={"a": {"id": "a", "x": 4, "y": 6}})
    draw = shape(
        "shape:d", "draw", segments=[{"type": "free", "points": [{"x": 1, "y": 2, "z": 0.5}]}]
    )
    scale_shape(line, 2)
    scale_shape(draw, 2)
    assert line["props"]["points"]["a"] == {"id": "a", "x": 8, "y": 12}
    assert draw["props"]["segments"][0]["points"][0] == {"x": 2, "y": 4, "z": 0.5}


def test_should_scale_images_and_frames_by_size() -> None:
    image = shape("shape:i", "image", w=64, h=32, crop=None)
    scale_shape(image, 1.5)
    assert image["props"] == {"w": 96, "h": 48, "crop": None}


def test_should_skip_values_that_are_not_numbers() -> None:
    record = shape("shape:x", "geo", w="10", h=True, scale=None)
    record["meta"] = "not a dict"
    scale_shape(record, 2)
    assert record["props"] == {"w": "10", "h": True, "scale": None}
