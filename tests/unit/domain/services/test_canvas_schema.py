import copy

import pytest

from app.domain.errors.domain_errors import InvalidInputError
from app.domain.services.canvas_schema import (
    ensure_same_versions,
    ensure_supports_images,
    first_page_id,
    sequences,
)
from tests.tldraw_records import SCHEMA, binding, geo, image_asset


def with_version(sequence: str, version: int | None) -> dict[str, object]:
    schema = copy.deepcopy(SCHEMA)
    if version is None:
        del schema["sequences"][sequence]
    else:
        schema["sequences"][sequence] = version
    return schema


def test_should_read_the_sequences_of_a_v2_schema() -> None:
    assert sequences(SCHEMA)["com.tldraw.shape.geo"] == 10
    assert sequences({"schemaVersion": 1, "sequences": {"a": 1}}) == {}
    assert sequences({"schemaVersion": 2, "sequences": "nope"}) == {}
    assert sequences(None) == {}


def test_should_accept_content_with_the_canvas_versions() -> None:
    records = [geo("shape:a"), binding("binding:a", "shape:a", "shape:a", "end")]
    ensure_same_versions(SCHEMA, SCHEMA, records + [image_asset("asset:a", "")])


def test_should_ignore_versions_of_records_the_content_does_not_have() -> None:
    ensure_same_versions(SCHEMA, with_version("com.tldraw.shape.note", 99), [geo("shape:a")])


@pytest.mark.parametrize(
    "canvas_schema",
    [
        with_version("com.tldraw.shape.geo", 11),
        with_version("com.tldraw.shape", 3),
        with_version("com.tldraw.shape.geo", None),
    ],
)
def test_should_refuse_content_saved_with_other_versions(canvas_schema: dict[str, object]) -> None:
    with pytest.raises(InvalidInputError, match="another version of the editor"):
        ensure_same_versions(SCHEMA, canvas_schema, [geo("shape:a")])


def test_should_refuse_bindings_and_assets_with_other_versions() -> None:
    with pytest.raises(InvalidInputError, match="com.tldraw.binding.arrow: 1 vs 2"):
        ensure_same_versions(
            SCHEMA,
            with_version("com.tldraw.binding.arrow", 2),
            [binding("binding:a", "shape:a", "shape:b", "end")],
        )


def test_should_refuse_content_without_a_schema() -> None:
    with pytest.raises(InvalidInputError, match="no editor schema"):
        ensure_same_versions(None, SCHEMA, [geo("shape:a")])


def test_should_accept_images_on_the_known_versions() -> None:
    ensure_supports_images(SCHEMA)


@pytest.mark.parametrize(
    "sequence",
    ["com.tldraw.shape.image", "com.tldraw.asset.image", "com.tldraw.shape", "com.tldraw.asset"],
)
def test_should_refuse_images_on_other_versions(sequence: str) -> None:
    with pytest.raises(InvalidInputError, match=sequence):
        ensure_supports_images(with_version(sequence, 99))


def test_should_pick_the_first_page_by_index() -> None:
    store = {
        "page:b": {"id": "page:b", "typeName": "page", "index": "a2"},
        "page:a": {"id": "page:a", "typeName": "page", "index": "a1"},
        "shape:x": geo("shape:x"),
    }
    assert first_page_id(store) == "page:a"


def test_should_refuse_a_canvas_without_pages() -> None:
    with pytest.raises(InvalidInputError, match="no page"):
        first_page_id({"shape:x": geo("shape:x")})
