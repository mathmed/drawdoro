from typing import Any


def rich_text(*paragraphs: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "attrs": {"dir": "auto"},
                "content": [{"type": "text", "text": text}],
            }
            for text in paragraphs
        ],
    }


def geo(
    shape_id: str, x: float, y: float, index: str, parent: str = "page:page", **meta: Any
) -> dict[str, Any]:
    return {
        "id": shape_id,
        "typeName": "shape",
        "type": "geo",
        "parentId": parent,
        "index": index,
        "x": x,
        "y": y,
        "rotation": 0,
        "isLocked": False,
        "opacity": 1,
        "meta": {"edges": "sharp"} | meta,
        "props": {
            "geo": "rectangle",
            "w": 200.4,
            "h": 80,
            "color": "blue",
            "richText": rich_text(),
        },
    }


def arrow_binding(binding_id: str, target: str, terminal: str) -> dict[str, Any]:
    return {
        "id": binding_id,
        "typeName": "binding",
        "type": "arrow",
        "fromId": "shape:arrow",
        "toId": target,
        "props": {"terminal": terminal},
        "meta": {},
    }


def sample_canvas_state() -> dict[str, Any]:
    api = geo("shape:api", 100, 40, "a1", fontSize=36)
    api["props"]["richText"] = rich_text("API")
    database = geo("shape:db", 100, 300, "a2")
    database["props"]["richText"] = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Database"}]},
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
                        ],
                    }
                    for text in ("orders", "payments")
                ],
            },
        ],
    }
    frame = geo("shape:frame", 600, 0, "a3")
    inside = geo("shape:inside", 20, 20, "a1", parent="shape:frame")
    arrow = {
        "id": "shape:arrow",
        "typeName": "shape",
        "type": "arrow",
        "parentId": "page:page",
        "index": "a4",
        "x": 200,
        "y": 120,
        "rotation": 0,
        "isLocked": False,
        "opacity": 1,
        "meta": {},
        "props": {"color": "black", "richText": rich_text("calls")},
    }
    line = {
        "id": "shape:line",
        "typeName": "shape",
        "type": "line",
        "parentId": "page:page",
        "index": "a5",
        "x": 50,
        "y": 500,
        "rotation": 0,
        "isLocked": False,
        "opacity": 1,
        "meta": {},
        "props": {
            "color": "grey",
            "points": {
                "a1": {"id": "a1", "index": "a1", "x": 0, "y": 0},
                "a2": {"id": "a2", "index": "a2", "x": 300, "y": -40},
            },
        },
    }
    records: list[dict[str, Any]] = [
        {"id": "document:document", "typeName": "document", "gridSize": 10, "name": "", "meta": {}},
        {"id": "page:page", "typeName": "page", "name": "Page 1", "index": "a1", "meta": {}},
        api,
        database,
        frame,
        inside,
        arrow,
        line,
        arrow_binding("binding:start", "shape:api", "start"),
        arrow_binding("binding:end", "shape:db", "end"),
    ]
    return {
        "store": {str(record["id"]): record for record in records},
        "schema": {"schemaVersion": 2, "sequences": {"com.tldraw.shape": 4}},
    }
