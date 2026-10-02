import base64
import copy
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from functools import reduce
from typing import Any

from app.domain.constants.canvas import CANVAS_FIRST_INDEX
from app.domain.entities.objects.bounds import Bounds
from app.domain.entities.objects.gallery_placement import GalleryPlacement
from app.domain.entities.objects.insertion_plan import InsertionPlan
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.placement_side import PlacementSide
from app.domain.errors.domain_errors import ConflictError, InvalidInputError
from app.domain.services.canvas_geometry import (
    CanvasRecord,
    children_by_parent,
    page_bounds,
    shape_bounds,
    union_bounds,
)
from app.domain.services.canvas_schema import (
    ensure_same_versions,
    ensure_supports_images,
    first_page_id,
)
from app.domain.services.fractional_index import indexes_above
from app.domain.services.gallery_item_measure import content_root_shapes
from app.domain.services.shape_scaling import scale_shape

ID_ATTEMPTS = 100
INVALID_CONTENT = "This gallery item has invalid shapes, so it can't be inserted"
SHAPE_DEFAULTS: CanvasRecord = {"rotation": 0, "isLocked": False, "opacity": 1, "meta": {}}


@dataclass(frozen=True)
class _Moves:
    origin: Bounds
    x: float
    y: float
    scale: float
    roots: set[str]


# Plans how a gallery item lands on a diagram's canvas without touching it: every record gets a
# new id that is not in the canvas (so inserting twice makes two copies and never overwrites
# anything), top-level shapes go on the first page above everything else, and positions are
# moved and scaled together so the copy keeps its layout.
class CanvasInsertion:
    def __init__(self, canvas_state: dict[str, Any], new_id: Callable[[], str]) -> None:
        self._schema = canvas_state.get("schema")
        self._store: dict[str, CanvasRecord] = dict(canvas_state.get("store") or {})
        self._page_id = first_page_id(self._store)
        self._new_id = new_id
        self._reserved: set[str] = set()
        self._indexes: Iterator[str] | None = None
        self._assets_by_source = _assets_by_source(self._store.values())

    def place_shapes(
        self, content: dict[str, Any], placement: GalleryPlacement, scale: float
    ) -> InsertionPlan:
        shapes = _shapes(content)
        bindings = _records(content.get("bindings"))
        assets = _records(content.get("assets"))
        ensure_same_versions(content.get("schema"), self._schema, shapes + bindings + assets)
        shape_ids = {str(shape["id"]): self._fresh_id("shape") for shape in shapes}
        roots = _roots(content, shapes)
        children = children_by_parent(shapes)
        _ensure_tree(shapes, roots, children)
        # Every shape hangs from a root, so there is at least one.
        origin = reduce(Bounds.union, (shape_bounds(root, children) for root in roots))
        width, height = origin.width * scale, origin.height * scale
        x, y = self._corner(placement, width, height)
        asset_ids, new_assets = self._copy_assets(assets)
        moves = _Moves(origin=origin, x=x, y=y, scale=scale, roots={str(r["id"]) for r in roots})
        placed = [
            self._place_shape(shape, shape_ids, asset_ids, moves)
            for shape in sorted(shapes, key=lambda shape: str(shape.get("index", "")))
        ]
        return InsertionPlan(
            records=new_assets + placed + _copy_bindings(bindings, shape_ids, self._fresh_id),
            root_shape_ids=[shape_ids[str(root["id"])] for root in roots],
            bounds=Bounds(x, y, x + width, y + height),
        )

    def place_image(
        self,
        data: bytes,
        mime_type: ImageMimeType,
        name: str,
        size: tuple[float, float],
        placement: GalleryPlacement,
        scale: float,
    ) -> InsertionPlan:
        ensure_supports_images(self._schema)
        width, height = size[0] * scale, size[1] * scale
        x, y = self._corner(placement, width, height)
        src = f"data:{mime_type};base64,{base64.b64encode(data).decode()}"
        asset = self._existing_asset(src)
        records: list[CanvasRecord] = []
        if asset is None:
            asset = _image_asset(self._fresh_id("asset"), src, mime_type, name, size, len(data))
            records.append(asset)
        shape = _image_shape(self._fresh_id("shape"), str(asset["id"]), width, height)
        records.append(shape | {"x": x, "y": y, "parentId": self._page_id, "index": self._index()})
        return InsertionPlan(
            records=records,
            root_shape_ids=[str(shape["id"])],
            bounds=Bounds(x, y, x + width, y + height),
        )

    def shape_count(self) -> int:
        return sum(1 for record in self._store.values() if record.get("typeName") == "shape")

    def _place_shape(
        self,
        shape: CanvasRecord,
        shape_ids: dict[str, str],
        asset_ids: dict[str, str],
        moves: _Moves,
    ) -> CanvasRecord:
        placed = SHAPE_DEFAULTS | copy.deepcopy(shape)
        placed |= {"id": shape_ids[str(shape["id"])], "typeName": "shape"}
        x, y = _coordinate(shape.get("x")), _coordinate(shape.get("y"))
        if str(shape["id"]) in moves.roots:
            placed |= {"parentId": self._page_id, "index": self._index()}
            placed |= {
                "x": moves.x + (x - moves.origin.min_x) * moves.scale,
                "y": moves.y + (y - moves.origin.min_y) * moves.scale,
            }
        else:
            # Children are positioned relative to their parent, which moves for them.
            placed |= {"parentId": shape_ids[str(shape.get("parentId"))]}
            placed |= {"x": x * moves.scale, "y": y * moves.scale}
        scale_shape(placed, moves.scale)
        if "assetId" in placed["props"] and placed["props"]["assetId"] is not None:
            placed["props"]["assetId"] = asset_ids.get(str(placed["props"]["assetId"]))
        return placed

    def _copy_assets(self, assets: list[CanvasRecord]) -> tuple[dict[str, str], list[CanvasRecord]]:
        ids: dict[str, str] = {}
        created: list[CanvasRecord] = []
        for asset in assets:
            existing = self._existing_asset((asset.get("props") or {}).get("src"))
            if existing is not None:
                ids[str(asset["id"])] = str(existing["id"])
                continue
            copied = copy.deepcopy(asset) | {"id": self._fresh_id("asset"), "typeName": "asset"}
            ids[str(asset["id"])] = copied["id"]
            created.append(copied)
            # Repeats of the same image inside the item share this copy too.
            self._assets_by_source.update(_assets_by_source([copied]))
        return ids, created

    # The same image inserted twice is stored once: big data URLs are most of a canvas's size.
    def _existing_asset(self, src: object) -> CanvasRecord | None:
        return self._assets_by_source.get(src) if isinstance(src, str) else None

    def _corner(
        self, placement: GalleryPlacement, width: float, height: float
    ) -> tuple[float, float]:
        has_point = placement.x is not None or placement.y is not None
        if placement.near_shape_id is not None and has_point:
            raise InvalidInputError("Pass either x and y or near_shape_id, not both")
        if placement.near_shape_id is not None:
            return self._next_to(placement, width, height)
        if placement.x is not None and placement.y is not None:
            return placement.x, placement.y
        if has_point:
            raise InvalidInputError("Pass both x and y, or neither")
        return self._beside_content(placement.gap)

    def _next_to(
        self, placement: GalleryPlacement, width: float, height: float
    ) -> tuple[float, float]:
        shape_id = str(placement.near_shape_id)
        if (self._store.get(shape_id) or {}).get("typeName") != "shape":
            raise InvalidInputError(f"{shape_id} is not a shape in this diagram")
        target = page_bounds(self._store, shape_id)
        gap = placement.gap
        corners = {
            PlacementSide.RIGHT: (target.max_x + gap, target.min_y),
            PlacementSide.LEFT: (target.min_x - gap - width, target.min_y),
            PlacementSide.BELOW: (target.min_x, target.max_y + gap),
            PlacementSide.ABOVE: (target.min_x, target.min_y - gap - height),
        }
        return corners[placement.side]

    # With no position given the copy goes to the right of everything on the page, top-aligned.
    def _beside_content(self, gap: float) -> tuple[float, float]:
        children = children_by_parent(self._store.values())
        content = union_bounds(
            shape_bounds(shape, children) for shape in children.get(self._page_id, [])
        )
        if content is None:
            return 0, 0
        return content.max_x + gap, content.min_y

    def _index(self) -> str:
        if self._indexes is None:
            self._indexes = indexes_above(self._top_index())
        try:
            return next(self._indexes)
        except StopIteration as exc:
            raise InvalidInputError("This item has too many shapes to insert at once") from exc

    def _top_index(self) -> str:
        indexes = [
            str(record["index"])
            for record in self._store.values()
            if record.get("typeName") == "shape"
            and record.get("parentId") == self._page_id
            and isinstance(record.get("index"), str)
        ]
        return max(indexes, default=CANVAS_FIRST_INDEX)

    def _fresh_id(self, prefix: str) -> str:
        for _ in range(ID_ATTEMPTS):
            candidate = f"{prefix}:{self._new_id()}"
            if candidate not in self._store and candidate not in self._reserved:
                self._reserved.add(candidate)
                return candidate
        raise ConflictError("Could not generate unique ids for the inserted records")


# Assets by their source, the first one of each; assets without a source are never shared.
def _assets_by_source(records: Iterable[CanvasRecord]) -> dict[str, CanvasRecord]:
    found: dict[str, CanvasRecord] = {}
    for record in records:
        props = record.get("props")
        src = props.get("src") if isinstance(props, dict) else None
        if record.get("typeName") == "asset" and isinstance(src, str) and src != "":
            found.setdefault(src, record)
    return found


def _records(value: object) -> list[CanvasRecord]:
    if not isinstance(value, list):
        return []
    return [
        record for record in value if isinstance(record, dict) and isinstance(record.get("id"), str)
    ]


def _shapes(content: dict[str, Any]) -> list[CanvasRecord]:
    shapes = content.get("shapes")
    if not isinstance(shapes, list) or not shapes:
        raise InvalidInputError(INVALID_CONTENT)
    for shape in shapes:
        if not _is_shape(shape):
            raise InvalidInputError(INVALID_CONTENT)
    # Two shapes with one id would become one record, leaving its children with two parents.
    if len({shape["id"] for shape in shapes}) != len(shapes):
        raise InvalidInputError(INVALID_CONTENT)
    return shapes


def _is_shape(shape: object) -> bool:
    return (
        isinstance(shape, dict)
        and isinstance(shape.get("id"), str)
        and str(shape["id"]).startswith("shape:")
        and isinstance(shape.get("type"), str)
        and isinstance(shape.get("props"), dict)
    )


# Saved roots, plus any shape whose parent wasn't saved with it, which would otherwise be lost.
def _roots(content: dict[str, Any], shapes: list[CanvasRecord]) -> list[CanvasRecord]:
    ids = {shape["id"] for shape in shapes}
    listed = {shape["id"] for shape in content_root_shapes(content)}
    roots = [shape for shape in shapes if shape["id"] in listed or shape.get("parentId") not in ids]
    return sorted(roots, key=lambda shape: str(shape.get("index", "")))


# Every saved shape must hang from a root: shapes whose parents loop back to them would be
# copied into the diagram as a broken tree that never reaches the page.
def _ensure_tree(
    shapes: list[CanvasRecord], roots: list[CanvasRecord], children: dict[str, list[CanvasRecord]]
) -> None:
    reached: set[str] = set()
    pending = [str(root["id"]) for root in roots]
    while pending:
        shape_id = pending.pop()
        if shape_id not in reached:
            reached.add(shape_id)
            pending.extend(str(child["id"]) for child in children.get(shape_id, []))
    if len(reached) != len(shapes):
        raise InvalidInputError(INVALID_CONTENT)


# Bindings tie an arrow to the shapes it connects; one with an end outside the item is dropped.
def _copy_bindings(
    bindings: list[CanvasRecord], shape_ids: dict[str, str], fresh_id: Callable[[str], str]
) -> list[CanvasRecord]:
    return [
        copy.deepcopy(binding)
        | {
            "id": fresh_id("binding"),
            "typeName": "binding",
            "fromId": shape_ids[str(binding.get("fromId"))],
            "toId": shape_ids[str(binding.get("toId"))],
        }
        for binding in bindings
        if str(binding.get("fromId")) in shape_ids and str(binding.get("toId")) in shape_ids
    ]


def _coordinate(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


# The same records the editor creates when an image file is dropped on the canvas.
def _image_asset(
    asset_id: str,
    src: str,
    mime_type: ImageMimeType,
    name: str,
    size: tuple[float, float],
    file_size: int,
) -> CanvasRecord:
    return {
        "id": asset_id,
        "typeName": "asset",
        "type": "image",
        "props": {
            "name": name,
            "src": src,
            "w": size[0],
            "h": size[1],
            "mimeType": str(mime_type),
            "isAnimated": mime_type == ImageMimeType.GIF,
            "fileSize": file_size,
        },
        "meta": {},
    }


def _image_shape(shape_id: str, asset_id: str, width: float, height: float) -> CanvasRecord:
    return SHAPE_DEFAULTS | {
        "id": shape_id,
        "typeName": "shape",
        "type": "image",
        "props": {
            "w": width,
            "h": height,
            "playing": True,
            "url": "",
            "assetId": asset_id,
            "crop": None,
            "flipX": False,
            "flipY": False,
            "altText": "",
        },
    }
