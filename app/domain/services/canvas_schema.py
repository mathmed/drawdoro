from collections.abc import Iterable
from typing import Any

from app.domain.errors.domain_errors import InvalidInputError
from app.domain.services.canvas_geometry import CanvasRecord

# Migration versions of the records the API writes itself (an image and its asset), as tldraw
# 3.15 serialises them. A canvas saved by a newer editor may expect fields these lack.
IMAGE_RECORD_VERSIONS = {
    "com.tldraw.shape": 4,
    "com.tldraw.shape.image": 5,
    "com.tldraw.asset": 1,
    "com.tldraw.asset.image": 5,
}
OUTDATED_ITEM = (
    "This gallery item was saved with another version of the editor than the diagram uses "
    "({sequence}: {item} vs {diagram}). Insert it from the Gallery panel in the editor, which "
    "upgrades it, or save it to the gallery again."
)


def sequences(schema: object) -> dict[str, int]:
    if not isinstance(schema, dict) or schema.get("schemaVersion") != 2:
        return {}
    found = schema.get("sequences")
    return dict(found) if isinstance(found, dict) else {}


# Saved content is copied into the canvas as is: the editor only migrates the canvas as a whole,
# from the canvas's versions, so records from another version would be read as the wrong one.
def ensure_same_versions(
    content_schema: object, canvas_schema: object, records: list[CanvasRecord]
) -> None:
    item_versions = sequences(content_schema)
    if not item_versions:
        raise InvalidInputError("This gallery item has no editor schema, so it can't be inserted")
    _compare(item_versions, sequences(canvas_schema), _sequences_used(records))


def ensure_supports_images(canvas_schema: object) -> None:
    _compare(IMAGE_RECORD_VERSIONS, sequences(canvas_schema), IMAGE_RECORD_VERSIONS)


def _compare(item: dict[str, int], diagram: dict[str, int], used: Iterable[str]) -> None:
    for sequence in used:
        if item.get(sequence) != diagram.get(sequence):
            raise InvalidInputError(
                OUTDATED_ITEM.format(
                    sequence=sequence, item=item.get(sequence), diagram=diagram.get(sequence)
                )
            )


def _sequences_used(records: list[CanvasRecord]) -> set[str]:
    used: set[str] = set()
    for record in records:
        type_name, record_type = record.get("typeName"), record.get("type")
        used.add(f"com.tldraw.{type_name}")
        used.add(f"com.tldraw.{type_name}.{record_type}")
    return used


def first_page_id(store: dict[str, Any]) -> str:
    pages = sorted(
        (record for record in store.values() if record.get("typeName") == "page"),
        key=lambda page: str(page.get("index", "")),
    )
    if not pages:
        raise InvalidInputError("The diagram's canvas has no page to insert into")
    return str(pages[0]["id"])
