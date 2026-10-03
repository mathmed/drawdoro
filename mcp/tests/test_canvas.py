from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from tools.canvas import Canvas, ShapeOutline, indexes_above, shape_size, shape_text

from tests.tldraw_records import rich_text


@pytest.fixture
def sut(canvas_state: dict[str, Any]) -> Canvas:
    return Canvas(canvas_state)


def stored(sut: Canvas, record_id: str) -> dict[str, Any]:
    record: dict[str, Any] = sut.to_snapshot()["store"][record_id]
    return record


def test_should_merge_patch_into_existing_record(sut: Canvas) -> None:
    created, changed = sut.upsert(
        [{"id": "shape:api", "meta": {"fontSize": 20}, "props": {"w": 90}}]
    )
    assert (created, changed) == ([], ["shape:api"])
    api = stored(sut, "shape:api")
    assert api["meta"] == {"edges": "sharp", "fontSize": 20}
    assert api["props"]["w"] == 90
    assert api["props"]["richText"] == rich_text("API")


def test_should_remove_keys_patched_with_null(sut: Canvas) -> None:
    sut.upsert([{"id": "shape:api", "meta": {"fontSize": None}}])
    assert stored(sut, "shape:api")["meta"] == {"edges": "sharp"}


def test_should_replace_lists_instead_of_merging_them(sut: Canvas) -> None:
    sut.upsert([{"id": "shape:api", "props": {"richText": rich_text("Gateway")}}])
    assert stored(sut, "shape:api")["props"]["richText"] == rich_text("Gateway")


def test_should_fill_the_envelope_of_new_shapes(sut: Canvas) -> None:
    props = {"geo": "rectangle", "w": 10, "h": 10, "richText": rich_text()}
    created, _ = sut.upsert([{"id": "shape:new", "type": "geo", "x": 5, "props": props}])
    assert created == ["shape:new"]
    new = stored(sut, "shape:new")
    assert new == {
        "id": "shape:new",
        "typeName": "shape",
        "type": "geo",
        "parentId": "page:page",
        "index": new["index"],
        "x": 5,
        "y": 0,
        "rotation": 0,
        "isLocked": False,
        "opacity": 1,
        "meta": {},
        "props": props,
    }


def test_should_stack_new_shapes_above_every_shape_in_creation_order(sut: Canvas) -> None:
    sut.upsert([{"id": f"shape:new{n}", "type": "geo", "props": {}} for n in range(3)])
    indexes = [stored(sut, f"shape:new{n}")["index"] for n in range(3)]
    assert indexes == sorted(indexes)
    assert min(indexes) > "a5"


def test_should_keep_given_index_and_parent(sut: Canvas) -> None:
    sut.upsert(
        [{"id": "shape:new", "type": "geo", "props": {}, "index": "a0V", "parentId": "shape:frame"}]
    )
    assert stored(sut, "shape:new")["index"] == "a0V"
    assert stored(sut, "shape:new")["parentId"] == "shape:frame"


@pytest.mark.parametrize(
    "record",
    [
        {"type": "geo", "props": {}},
        {"id": "", "type": "geo", "props": {}},
        {"id": "shape:new", "props": {}},
        {"id": "shape:new", "type": "geo"},
        {"id": "binding:new", "type": "arrow", "fromId": "shape:arrow", "toId": "shape:api"},
    ],
)
def test_should_reject_incomplete_new_records(sut: Canvas, record: dict[str, Any]) -> None:
    with pytest.raises(ToolError):
        sut.upsert([record])


def test_should_delete_children_and_bindings_along_with_a_shape(sut: Canvas) -> None:
    assert sut.delete(["shape:frame", "shape:api"]) == [
        "binding:start",
        "shape:api",
        "shape:frame",
        "shape:inside",
    ]
    assert set(sut.to_snapshot()["store"]) == {
        "document:document",
        "page:page",
        "shape:db",
        "shape:arrow",
        "shape:line",
        "binding:end",
    }


def test_should_reject_deleting_unknown_ids(sut: Canvas) -> None:
    with pytest.raises(ToolError, match="shape:ghost"):
        sut.delete(["shape:api", "shape:ghost"])
    assert "shape:api" in sut.to_snapshot()["store"]


def test_should_not_delete_the_document(sut: Canvas) -> None:
    with pytest.raises(ToolError):
        sut.delete(["document:document"])


@pytest.mark.parametrize("canvas_state", [None, {}, {"store": {}}])
def test_should_refuse_a_canvas_that_was_never_saved(canvas_state: dict[str, Any] | None) -> None:
    with pytest.raises(ToolError, match="no canvas yet"):
        Canvas(canvas_state)


def test_should_outline_shapes_in_reading_order(sut: Canvas) -> None:
    assert [shape.id for shape in sut.outline()] == [
        "shape:frame",
        "shape:inside",
        "shape:api",
        "shape:arrow",
        "shape:db",
        "shape:line",
    ]


def test_should_outline_the_details_of_each_kind_of_shape(sut: Canvas) -> None:
    shapes = {shape.id: shape for shape in sut.outline()}
    assert shapes["shape:api"] == ShapeOutline(
        id="shape:api",
        type="geo",
        x=100,
        y=40,
        w=200,
        h=80,
        geo="rectangle",
        color="blue",
        font_size=36,
        text="API",
    )
    assert shapes["shape:db"].text == "Database\n- orders\n- payments"
    assert shapes["shape:inside"].parent == "shape:frame"
    assert (shapes["shape:arrow"].start, shapes["shape:arrow"].end) == ("shape:api", "shape:db")
    assert (shapes["shape:line"].w, shapes["shape:line"].h) == (300, 40)


def test_should_leave_missing_fields_out_of_the_outline(sut: Canvas) -> None:
    frame = next(shape for shape in sut.outline() if shape.id == "shape:frame")
    assert frame.model_dump() == {
        "id": "shape:frame",
        "type": "geo",
        "x": 600,
        "y": 0,
        "w": 200,
        "h": 80,
        "geo": "rectangle",
        "color": "blue",
    }


def test_should_read_plain_text_props() -> None:
    assert shape_text({"text": "legacy"}) == "legacy"
    assert shape_text({"text": ""}) is None
    assert shape_text({}) is None


def test_should_generate_valid_indexes_above_the_top_one() -> None:
    indexes = list(indexes_above("b1C"))
    assert indexes == sorted(indexes)
    assert all(index > "b1C" and not index.endswith("0") for index in indexes)


def test_should_store_a_new_non_shape_record_as_given(sut: Canvas) -> None:
    binding = {"id": "binding:new", "typeName": "binding", "fromId": "shape:api"}
    created, _ = sut.upsert([binding])
    assert created == ["binding:new"]
    assert stored(sut, "binding:new") == binding


def test_should_refuse_a_new_non_shape_record_without_its_type_name(sut: Canvas) -> None:
    with pytest.raises(ToolError, match="binding:new is new, so it must be a complete"):
        sut.upsert([{"id": "binding:new", "fromId": "shape:api"}])


@pytest.mark.parametrize("record", [{"type": "geo"}, {"props": {}}])
def test_should_refuse_a_new_shape_without_its_type_or_props(
    sut: Canvas, record: dict[str, Any]
) -> None:
    with pytest.raises(ToolError, match="shape:new is new, so it needs at least its type"):
        sut.upsert([{"id": "shape:new", **record}])


def test_should_delete_a_binding_that_starts_at_a_deleted_shape(sut: Canvas) -> None:
    sut.upsert([{"id": "binding:out", "typeName": "binding", "fromId": "shape:api", "toId": "x"}])
    assert "binding:out" in sut.delete(["shape:api"])
    assert "binding:out" not in sut.to_snapshot()["store"]


def test_should_keep_bindings_and_shapes_unrelated_to_the_deleted_ones(sut: Canvas) -> None:
    sut.upsert([{"id": "binding:other", "typeName": "binding", "fromId": "a", "toId": "b"}])
    sut.delete(["shape:api"])
    assert "binding:other" in sut.to_snapshot()["store"]


@pytest.mark.parametrize(
    ("props", "expected"),
    [
        ({"points": {"a": {"x": 0, "y": 0}, "b": {"x": 10.4, "y": -5}}}, (10, 5)),
        ({"points": {"a": {"x": 3}}}, (0, 0)),
        ({"points": {}, "w": 4.6, "h": 2}, (5, 2)),
        ({"w": "wide", "h": None}, (None, None)),
        ({}, (None, None)),
    ],
)
def test_should_measure_a_shape_from_its_points_or_its_size(
    props: dict[str, Any], expected: tuple[int | None, int | None]
) -> None:
    assert shape_size(props) == expected
