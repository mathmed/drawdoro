from app.domain.entities.objects.bounds import Bounds
from app.domain.services.canvas_geometry import (
    children_by_parent,
    local_bounds,
    page_bounds,
    shape_bounds,
    shape_points,
    union_bounds,
)
from tests.tldraw_records import PAGE_ID, arrow, geo, group, shape


def test_should_measure_shapes_with_a_size() -> None:
    assert local_bounds(geo("shape:a", w=120, h=60)) == Bounds(0, 0, 120, 60)


def test_should_fall_back_to_a_default_size() -> None:
    assert local_bounds(shape("shape:a", "embed")) == Bounds(0, 0, 100, 100)
    assert local_bounds(shape("shape:a", "embed", w="wide", h=True)) == Bounds(0, 0, 100, 100)


def test_should_size_sticky_notes_from_their_scale_and_growth() -> None:
    assert local_bounds(shape("shape:n", "note", scale=2, growY=50)) == Bounds(0, 0, 400, 500)
    assert local_bounds(shape("shape:n", "note")) == Bounds(0, 0, 200, 200)


def test_should_estimate_text_from_its_width_and_scale() -> None:
    assert local_bounds(shape("shape:t", "text", w=150, scale=2)) == Bounds(0, 0, 300, 80)


def test_should_span_the_points_of_arrows_lines_and_drawings() -> None:
    assert local_bounds(arrow("shape:a", 0, 0, (-30, 40))) == Bounds(-30, 0, 0, 40)
    line = shape("shape:l", "line", points={"a": {"x": 5, "y": -5}, "b": {"x": 50, "y": 10}})
    assert local_bounds(line) == Bounds(5, -5, 50, 10)
    draw = shape(
        "shape:d",
        "draw",
        segments=[{"points": [{"x": 1, "y": 2}, {"x": 9, "y": 4}]}, {"points": [{"x": 3, "y": 8}]}],
    )
    assert local_bounds(draw) == Bounds(1, 2, 9, 8)


def test_should_ignore_malformed_points() -> None:
    assert shape_points("line", {"points": [1, 2]}) == []
    assert shape_points("draw", {"segments": ["x", {"points": ["y", {"x": 1, "y": 1}]}]}) == [
        {"x": 1, "y": 1}
    ]
    assert shape_points("arrow", {"start": None, "end": {"x": 2, "y": 3}}) == [{"x": 2, "y": 3}]
    assert shape_points("geo", {"points": {"a": {"x": 1, "y": 1}}}) == []


def test_should_place_bounds_at_the_shape_position() -> None:
    assert shape_bounds(geo("shape:a", 10, 20, 30, 40), {}) == Bounds(10, 20, 40, 60)


def test_should_span_the_children_of_a_group() -> None:
    records = [
        group("shape:g", 100, 100),
        geo("shape:a", 0, 0, 50, 50, parent="shape:g"),
        geo("shape:b", 100, 20, 50, 50, parent="shape:g"),
    ]
    assert shape_bounds(records[0], children_by_parent(records)) == Bounds(100, 100, 250, 170)


def test_should_give_an_empty_group_the_default_size() -> None:
    assert shape_bounds(group("shape:g", 5, 5), {}) == Bounds(5, 5, 105, 105)


def test_should_index_only_shapes_by_parent() -> None:
    records = [geo("shape:a"), {"id": "binding:x", "typeName": "binding", "parentId": PAGE_ID}]
    assert children_by_parent(records) == {PAGE_ID: [records[0]]}


def test_should_add_the_positions_of_every_ancestor_for_page_bounds() -> None:
    store = {
        PAGE_ID: {"id": PAGE_ID, "typeName": "page"},
        "shape:frame": geo("shape:frame", 100, 200, 500, 500),
        "shape:g": group("shape:g", 10, 20) | {"parentId": "shape:frame"},
        "shape:a": geo("shape:a", 1, 2, 30, 40, parent="shape:g"),
    }
    assert page_bounds(store, "shape:a") == Bounds(111, 222, 141, 262)


def test_should_survive_a_parent_cycle() -> None:
    store = {
        "shape:a": geo("shape:a", 1, 1, 10, 10, parent="shape:b"),
        "shape:b": geo("shape:b", 5, 5, 10, 10, parent="shape:a"),
    }
    assert page_bounds(store, "shape:a") == Bounds(6, 6, 16, 16)


def test_should_union_bounds() -> None:
    assert union_bounds([]) is None
    assert union_bounds([Bounds(0, 5, 10, 10), Bounds(-5, 0, 3, 20)]) == Bounds(-5, 0, 10, 20)
    assert Bounds(1, 2, 4, 8).width == 3
    assert Bounds(1, 2, 4, 8).height == 6
