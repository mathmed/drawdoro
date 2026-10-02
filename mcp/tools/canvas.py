from collections.abc import Iterator
from itertools import product

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer
from tools.api import JsonObject

# Digits of tldraw's fractional indexes (the order of shapes), in sort order.
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
FIRST_INDEX = "a1"
SHAPE_DEFAULTS: JsonObject = {"rotation": 0, "isLocked": False, "opacity": 1, "meta": {}}
LIST_NODES = {"bulletList", "orderedList", "taskList"}


class ShapeOutline(BaseModel):
    id: str
    type: str
    x: int
    y: int
    w: int | None = None
    h: int | None = None
    parent: str | None = None
    geo: str | None = None
    color: str | None = None
    font_size: int | None = None
    text: str | None = None
    start: str | None = None
    end: str | None = None

    # The outline exists to be small: fields a shape does not have are left out entirely.
    @model_serializer(mode="wrap")
    def _without_empty_fields(self, handler: SerializerFunctionWrapHandler) -> JsonObject:
        return {key: value for key, value in handler(self).items() if value is not None}


class Canvas:
    def __init__(self, canvas_state: JsonObject | None) -> None:
        if not canvas_state or "schema" not in canvas_state:
            raise ToolError(
                "The diagram has no canvas yet: open it once in the editor, or send the whole "
                "canvas_state with update_diagram"
            )
        self._schema = canvas_state["schema"]
        self._store: dict[str, JsonObject] = dict(canvas_state.get("store", {}))
        self._new_indexes: Iterator[str] | None = None

    def to_snapshot(self) -> JsonObject:
        return {"store": self._store, "schema": self._schema}

    def record_count(self) -> int:
        return len(self._store)

    def upsert(self, records: list[JsonObject]) -> tuple[list[str], list[str]]:
        created: list[str] = []
        changed: list[str] = []
        for record in records:
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id:
                raise ToolError(f"Every record in upsert needs its id, got: {record}")
            current = self._store.get(record_id)
            if current is None:
                self._store[record_id] = self._complete(record)
                created.append(record_id)
            else:
                self._store[record_id] = merge_patch(current, record)
                changed.append(record_id)
        return created, changed

    def delete(self, record_ids: list[str]) -> list[str]:
        unknown = [record_id for record_id in record_ids if record_id not in self._store]
        if unknown:
            raise ToolError(f"Not in the diagram: {', '.join(unknown)}")
        if any(record_id.startswith("document:") for record_id in record_ids):
            raise ToolError("The document record cannot be deleted")
        doomed = self._with_descendants(record_ids)
        # An arrow binding pointing at a deleted shape would leave the arrow attached to nothing.
        doomed |= {
            record_id
            for record_id, record in self._store.items()
            if record.get("typeName") == "binding"
            and (record.get("fromId") in doomed or record.get("toId") in doomed)
        }
        for record_id in doomed:
            del self._store[record_id]
        return sorted(doomed)

    def outline(self) -> list[ShapeOutline]:
        bindings = self._arrow_ends()
        shapes = [
            self._outline_shape(record, bindings)
            for record in self._store.values()
            if record.get("typeName") == "shape"
        ]
        return sorted(shapes, key=lambda shape: (shape.y, shape.x))

    def _complete(self, record: JsonObject) -> JsonObject:
        record_id = str(record["id"])
        if not record_id.startswith("shape:"):
            if "typeName" not in record:
                raise ToolError(f"{record_id} is new, so it must be a complete tldraw record")
            return record
        if "type" not in record or "props" not in record:
            raise ToolError(f"{record_id} is new, so it needs at least its type and complete props")
        defaults: JsonObject = SHAPE_DEFAULTS | {
            "typeName": "shape",
            "parentId": self._first_page_id(),
            "x": 0,
            "y": 0,
        }
        if "index" not in record:
            defaults["index"] = self._next_index()
        return defaults | record

    def _first_page_id(self) -> str:
        pages = sorted(
            (record for record in self._store.values() if record.get("typeName") == "page"),
            key=lambda page: str(page.get("index", "")),
        )
        if not pages:
            raise ToolError("The canvas has no page to put new shapes on")
        return str(pages[0]["id"])

    def _next_index(self) -> str:
        if self._new_indexes is None:
            self._new_indexes = indexes_above(self._top_index())
        try:
            return next(self._new_indexes)
        except StopIteration as exc:
            raise ToolError(
                "Too many new shapes in one call; split them in smaller batches"
            ) from exc

    def _top_index(self) -> str:
        indexes = [
            str(record["index"])
            for record in self._store.values()
            if record.get("typeName") == "shape" and "index" in record
        ]
        return max(indexes, default=FIRST_INDEX)

    def _with_descendants(self, record_ids: list[str]) -> set[str]:
        doomed: set[str] = set()
        pending = list(record_ids)
        while pending:
            record_id = pending.pop()
            if record_id in doomed:
                continue
            doomed.add(record_id)
            pending.extend(
                child_id
                for child_id, child in self._store.items()
                if child.get("parentId") == record_id
            )
        return doomed

    def _arrow_ends(self) -> dict[tuple[str, str], str]:
        ends: dict[tuple[str, str], str] = {}
        for record in self._store.values():
            if record.get("typeName") != "binding" or record.get("type") != "arrow":
                continue
            terminal = record.get("props", {}).get("terminal")
            if terminal in ("start", "end"):
                ends[(str(record["fromId"]), terminal)] = str(record["toId"])
        return ends

    def _outline_shape(
        self, record: JsonObject, arrow_ends: dict[tuple[str, str], str]
    ) -> ShapeOutline:
        props: JsonObject = record.get("props", {})
        meta: JsonObject = record.get("meta", {})
        width, height = shape_size(props)
        parent = str(record.get("parentId", ""))
        font_size = meta.get("fontSize")
        return ShapeOutline(
            id=str(record["id"]),
            type=str(record.get("type", "")),
            x=round(record.get("x", 0)),
            y=round(record.get("y", 0)),
            w=width,
            h=height,
            parent=None if parent.startswith("page:") else parent or None,
            geo=props.get("geo"),
            color=props.get("color"),
            font_size=round(font_size) if isinstance(font_size, int | float) else None,
            text=shape_text(props),
            start=arrow_ends.get((str(record["id"]), "start")),
            end=arrow_ends.get((str(record["id"]), "end")),
        )


def merge_patch(target: JsonObject, patch: JsonObject) -> JsonObject:
    # JSON Merge Patch (RFC 7386): objects merge key by key, null removes a key, anything else
    # (lists included) replaces the stored value.
    merged = dict(target)
    for key, value in patch.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_patch(merged[key], value)
        else:
            merged[key] = value
    return merged


def indexes_above(top: str) -> Iterator[str]:
    # Any key that extends `top` sorts after it and after every existing key, because `top` is
    # the largest one. A fractional index may not end in "0", so the last digit never is.
    for first, last in product(BASE62, BASE62[1:]):
        yield f"{top}{first}{last}"


def shape_text(props: JsonObject) -> str | None:
    rich_text = props.get("richText")
    if isinstance(rich_text, dict):
        text = "\n".join(_blocks(rich_text)).strip()
        return text or None
    plain = props.get("text")
    if isinstance(plain, str) and plain:
        return plain
    return None


def _blocks(node: JsonObject, prefix: str = "") -> Iterator[str]:
    node_type = node.get("type")
    children: list[JsonObject] = node.get("content", [])
    if node_type in ("paragraph", "heading"):
        yield prefix + "".join(_inline(child) for child in children)
        return
    for child in children:
        yield from _blocks(child, "- " if node_type in LIST_NODES else prefix)


def _inline(node: JsonObject) -> str:
    if node.get("type") == "hardBreak":
        return "\n"
    text = node.get("text")
    return text if isinstance(text, str) else ""


def shape_size(props: JsonObject) -> tuple[int | None, int | None]:
    points = props.get("points")
    if isinstance(points, dict) and points:
        xs = [point.get("x", 0) for point in points.values()]
        ys = [point.get("y", 0) for point in points.values()]
        return round(max(xs) - min(xs)), round(max(ys) - min(ys))
    width = props.get("w")
    height = props.get("h")
    return (
        round(width) if isinstance(width, int | float) else None,
        round(height) if isinstance(height, int | float) else None,
    )
