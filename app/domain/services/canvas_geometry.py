from collections.abc import Iterable, Mapping
from typing import Any

from app.domain.constants.canvas import CANVAS_FALLBACK_SIZE, CANVAS_NOTE_SIZE
from app.domain.entities.objects.bounds import Bounds

type CanvasRecord = dict[str, Any]

# A text shape's height comes from its rendered text; one line at the default size is close.
TEXT_LINE_HEIGHT = 40

# Approximate bounds of tldraw shapes, enough to place things without overlap: rotation is ignored
# and sizes the editor measures itself (text, sticky notes) are estimated.


def children_by_parent(records: Iterable[CanvasRecord]) -> dict[str, list[CanvasRecord]]:
    children: dict[str, list[CanvasRecord]] = {}
    for record in records:
        if record.get("typeName") == "shape":
            children.setdefault(str(record.get("parentId")), []).append(record)
    return children


# Bounds of a shape in its parent's coordinates. Groups have no size of their own: they span
# their children.
def shape_bounds(record: CanvasRecord, children: Mapping[str, list[CanvasRecord]]) -> Bounds:
    return _shape_bounds(record, children, frozenset())


def _shape_bounds(
    record: CanvasRecord, children: Mapping[str, list[CanvasRecord]], ancestors: frozenset[str]
) -> Bounds:
    x, y = _number(record.get("x")), _number(record.get("y"))
    shape_id = str(record.get("id"))
    # A broken canvas could make a group its own ancestor: the loop is cut where it repeats.
    if record.get("type") == "group" and shape_id not in ancestors:
        inside = ancestors | {shape_id}
        inner = union_bounds(
            _shape_bounds(child, children, inside) for child in children.get(shape_id, [])
        )
        if inner is not None:
            return inner.translated(x, y)
    return local_bounds(record).translated(x, y)


def union_bounds(bounds: Iterable[Bounds]) -> Bounds | None:
    result: Bounds | None = None
    for box in bounds:
        result = box if result is None else result.union(box)
    return result


# Bounds of a shape in page coordinates, through the chain of groups and frames it is in.
def page_bounds(store: Mapping[str, CanvasRecord], shape_id: str) -> Bounds:
    record = store[shape_id]
    bounds = shape_bounds(record, children_by_parent(store.values()))
    seen = {shape_id}
    parent = store.get(str(record.get("parentId")))
    # A broken canvas could make shapes their own ancestors; each one counts once.
    while parent is not None and parent.get("typeName") == "shape" and parent["id"] not in seen:
        seen.add(parent["id"])
        bounds = bounds.translated(_number(parent.get("x")), _number(parent.get("y")))
        parent = store.get(str(parent.get("parentId")))
    return bounds


def local_bounds(record: CanvasRecord) -> Bounds:
    props: dict[str, Any] = record.get("props") or {}
    points = shape_points(record.get("type"), props)
    if points:
        xs = [_number(point.get("x")) for point in points]
        ys = [_number(point.get("y")) for point in points]
        return Bounds(min(xs), min(ys), max(xs), max(ys))
    width, height = _size(record.get("type"), props)
    return Bounds(0, 0, width, height)


def _size(shape_type: object, props: dict[str, Any]) -> tuple[float, float]:
    scale = _number(props.get("scale"), 1)
    if shape_type == "note":
        return CANVAS_NOTE_SIZE * scale, (CANVAS_NOTE_SIZE + _number(props.get("growY"))) * scale
    if shape_type == "text":
        return _number(props.get("w"), CANVAS_FALLBACK_SIZE) * scale, TEXT_LINE_HEIGHT * scale
    return (
        _number(props.get("w"), CANVAS_FALLBACK_SIZE),
        _number(props.get("h"), CANVAS_FALLBACK_SIZE),
    )


# The points that make up arrows, lines and freehand drawings, relative to the shape.
def shape_points(shape_type: object, props: dict[str, Any]) -> list[dict[str, Any]]:
    reader = _POINT_READERS.get(str(shape_type))
    return _only_points(reader(props)) if reader is not None else []


def _arrow_points(props: dict[str, Any]) -> list[object]:
    return [props.get("start"), props.get("end")]


def _line_points(props: dict[str, Any]) -> list[object]:
    points = props.get("points")
    return list(points.values()) if isinstance(points, dict) else []


def _draw_points(props: dict[str, Any]) -> list[object]:
    segments = props.get("segments")
    if not isinstance(segments, list):
        return []
    return [point for segment in _only_points(segments) for point in segment.get("points", [])]


def _only_points(values: list[object]) -> list[dict[str, Any]]:
    return [value for value in values if isinstance(value, dict)]


_POINT_READERS = {
    "arrow": _arrow_points,
    "line": _line_points,
    "draw": _draw_points,
    "highlight": _draw_points,
}


def _number(value: object, default: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return default
    return float(value)
