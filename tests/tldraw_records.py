import struct
import zlib
from typing import Any

# The schema tldraw 3.15 serialises with every canvas and gallery item.
SCHEMA: dict[str, Any] = {
    "schemaVersion": 2,
    "sequences": {
        "com.tldraw.store": 4,
        "com.tldraw.asset": 1,
        "com.tldraw.camera": 1,
        "com.tldraw.document": 2,
        "com.tldraw.instance": 25,
        "com.tldraw.instance_page_state": 5,
        "com.tldraw.page": 1,
        "com.tldraw.instance_presence": 6,
        "com.tldraw.pointer": 1,
        "com.tldraw.shape": 4,
        "com.tldraw.asset.bookmark": 2,
        "com.tldraw.asset.image": 5,
        "com.tldraw.asset.video": 5,
        "com.tldraw.shape.arrow": 6,
        "com.tldraw.shape.bookmark": 2,
        "com.tldraw.shape.draw": 2,
        "com.tldraw.shape.embed": 4,
        "com.tldraw.shape.frame": 1,
        "com.tldraw.shape.geo": 10,
        "com.tldraw.shape.group": 0,
        "com.tldraw.shape.highlight": 1,
        "com.tldraw.shape.image": 5,
        "com.tldraw.shape.line": 5,
        "com.tldraw.shape.note": 9,
        "com.tldraw.shape.text": 3,
        "com.tldraw.shape.video": 4,
        "com.tldraw.binding.arrow": 1,
    },
}
PAGE_ID = "page:page"


def page(page_id: str = PAGE_ID, index: str = "a1") -> dict[str, Any]:
    return {"id": page_id, "typeName": "page", "name": "Page 1", "index": index, "meta": {}}


def canvas(*records: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    document = {
        "id": "document:document",
        "typeName": "document",
        "gridSize": 10,
        "name": "",
        "meta": {},
    }
    store = {document["id"]: document, PAGE_ID: page()}
    store.update({record["id"]: record for record in records})
    return {"store": store, "schema": SCHEMA if schema is None else schema}


def shape(
    shape_id: str,
    shape_type: str,
    x: float = 0,
    y: float = 0,
    parent: str = PAGE_ID,
    index: str = "a1",
    **props: Any,
) -> dict[str, Any]:
    return {
        "id": shape_id,
        "typeName": "shape",
        "type": shape_type,
        "parentId": parent,
        "index": index,
        "x": x,
        "y": y,
        "rotation": 0,
        "isLocked": False,
        "opacity": 1,
        "meta": {},
        "props": props,
    }


def geo(
    shape_id: str,
    x: float = 0,
    y: float = 0,
    w: float = 100,
    h: float = 50,
    parent: str = PAGE_ID,
    index: str = "a1",
) -> dict[str, Any]:
    return shape(shape_id, "geo", x, y, parent, index, geo="rectangle", w=w, h=h, scale=1)


def group(shape_id: str, x: float = 0, y: float = 0, index: str = "a1") -> dict[str, Any]:
    return shape(shape_id, "group", x, y, PAGE_ID, index)


def arrow(
    shape_id: str, x: float, y: float, end: tuple[float, float], index: str = "a1"
) -> dict[str, Any]:
    return shape(
        shape_id,
        "arrow",
        x,
        y,
        PAGE_ID,
        index,
        start={"x": 0, "y": 0},
        end={"x": end[0], "y": end[1]},
        bend=0,
        scale=1,
    )


def binding(binding_id: str, arrow_id: str, target: str, terminal: str) -> dict[str, Any]:
    return {
        "id": binding_id,
        "typeName": "binding",
        "type": "arrow",
        "fromId": arrow_id,
        "toId": target,
        "props": {"terminal": terminal, "isExact": False, "isPrecise": False},
        "meta": {},
    }


def image_asset(asset_id: str, src: str) -> dict[str, Any]:
    return {
        "id": asset_id,
        "typeName": "asset",
        "type": "image",
        "props": {
            "name": "logo.png",
            "src": src,
            "w": 64,
            "h": 32,
            "mimeType": "image/png",
            "isAnimated": False,
        },
        "meta": {},
    }


def content(
    shapes: list[dict[str, Any]],
    bindings: list[dict[str, Any]] | None = None,
    assets: list[dict[str, Any]] | None = None,
    roots: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "shapes": shapes,
        "bindings": bindings or [],
        "assets": assets or [],
        "rootShapeIds": roots
        if roots is not None
        else [s["id"] for s in shapes if s["parentId"] == PAGE_ID],
    }


# Largest image png() builds: its pixel buffer takes about width x height bytes of memory.
PNG_MAX_PIXELS = 1_000_000


# A real, decodable, all-grey PNG of the given size. It holds every pixel, so it refuses sizes
# above PNG_MAX_PIXELS: build only the header by hand to test larger sizes.
def png(width: int, height: int) -> bytes:
    if width * height > PNG_MAX_PIXELS:
        raise ValueError(
            f"png({width}, {height}) would allocate a buffer of {width * height} bytes"
        )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    pixels = zlib.compress(b"".join(b"\x00" + b"\x80" * width for _ in range(height)))
    return (
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")
    )
