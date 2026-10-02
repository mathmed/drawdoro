import base64
import copy
from collections.abc import Callable, Iterator
from itertools import count
from typing import Any

import pytest

from app.domain.entities.objects.bounds import Bounds
from app.domain.entities.objects.gallery_placement import GalleryPlacement
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.placement_side import PlacementSide
from app.domain.errors.domain_errors import ConflictError, InvalidInputError
from app.domain.services import canvas_geometry, canvas_insertion
from app.domain.services.canvas_insertion import CanvasInsertion
from tests.tldraw_records import (
    PAGE_ID,
    SCHEMA,
    arrow,
    binding,
    canvas,
    content,
    geo,
    group,
    image_asset,
    png,
    shape,
)

AUTO = GalleryPlacement()
DATA_URL = "data:image/png;base64,AAAA"


def sequential_ids() -> Callable[[], str]:
    numbers: Iterator[int] = count(1)
    return lambda: f"n{next(numbers)}"


def make_sut(*records: dict[str, Any]) -> CanvasInsertion:
    return CanvasInsertion(canvas(*records), sequential_ids())


def by_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in records}


@pytest.fixture
def sut() -> CanvasInsertion:
    return make_sut(geo("shape:existing", 0, 0, 100, 50, index="a5"))


def test_should_copy_a_shape_with_a_new_id_on_the_first_page(sut: CanvasInsertion) -> None:
    saved = content([geo("shape:a", 300, 300, 40, 20, index="a1")])
    original = copy.deepcopy(saved)

    plan = sut.place_shapes(saved, AUTO, 1)

    placed = plan.records[0]
    assert plan.created_ids == ["shape:n1"]
    assert plan.root_shape_ids == ["shape:n1"]
    assert (placed["id"], placed["typeName"], placed["parentId"]) == ("shape:n1", "shape", PAGE_ID)
    assert placed["index"] == "a501"
    assert placed["props"] == {"geo": "rectangle", "w": 40, "h": 20, "scale": 1}
    assert saved == original


def test_should_place_it_right_of_everything_by_default(sut: CanvasInsertion) -> None:
    plan = sut.place_shapes(content([geo("shape:a", 300, 300, 40, 20)]), AUTO, 1)

    assert (plan.records[0]["x"], plan.records[0]["y"]) == (180, 0)
    assert plan.bounds == Bounds(180, 0, 220, 20)


def test_should_use_the_gap_of_the_placement(sut: CanvasInsertion) -> None:
    plan = sut.place_shapes(content([geo("shape:a")]), GalleryPlacement(gap=10), 1)
    assert plan.records[0]["x"] == 110


def test_should_start_at_the_origin_of_an_empty_page() -> None:
    plan = make_sut().place_shapes(content([geo("shape:a", 300, 300)]), AUTO, 1)

    assert (plan.records[0]["x"], plan.records[0]["y"]) == (0, 0)
    assert plan.records[0]["index"] == "a101"


def test_should_move_shapes_together_to_the_given_corner(sut: CanvasInsertion) -> None:
    saved = content([geo("shape:a", 100, 50, 40, 20), geo("shape:b", 200, 150, 40, 20, index="a2")])

    plan = sut.place_shapes(saved, GalleryPlacement(x=1000, y=-500), 1)

    placed = by_id(plan.records)
    assert (placed["shape:n1"]["x"], placed["shape:n1"]["y"]) == (1000, -500)
    assert (placed["shape:n2"]["x"], placed["shape:n2"]["y"]) == (1100, -400)
    assert plan.bounds == Bounds(1000, -500, 1140, -380)


def test_should_scale_positions_sizes_and_bounds(sut: CanvasInsertion) -> None:
    saved = content([geo("shape:a", 100, 50, 40, 20), geo("shape:b", 200, 150, 40, 20, index="a2")])

    plan = sut.place_shapes(saved, GalleryPlacement(x=0, y=0), 2)

    placed = by_id(plan.records)
    assert (placed["shape:n2"]["x"], placed["shape:n2"]["y"]) == (200, 200)
    assert (placed["shape:n2"]["props"]["w"], placed["shape:n2"]["props"]["h"]) == (80, 40)
    assert plan.bounds == Bounds(0, 0, 280, 240)


def test_should_keep_groups_with_their_children(sut: CanvasInsertion) -> None:
    saved = content(
        [
            group("shape:g", 500, 500),
            geo("shape:a", 0, 0, 50, 50, parent="shape:g", index="a1"),
            geo("shape:b", 100, 0, 50, 50, parent="shape:g", index="a2"),
        ]
    )

    plan = sut.place_shapes(saved, GalleryPlacement(x=10, y=20), 2)

    placed = by_id(plan.records)
    new_group = plan.root_shape_ids[0]
    assert placed[new_group]["type"] == "group"
    assert (placed[new_group]["x"], placed[new_group]["y"], placed[new_group]["parentId"]) == (
        10,
        20,
        PAGE_ID,
    )
    children = [record for record in plan.records if record["parentId"] == new_group]
    assert sorted((child["x"], child["y"]) for child in children) == [(0, 0), (200, 0)]
    assert all("index" in child and child["index"] in ("a1", "a2") for child in children)
    assert plan.bounds == Bounds(10, 20, 310, 120)


def test_should_reconnect_arrows_to_the_copied_shapes(sut: CanvasInsertion) -> None:
    saved = content(
        [
            geo("shape:api", 0, 0, index="a1"),
            geo("shape:db", 300, 0, index="a2"),
            arrow("shape:arrow", 100, 25, (200, 0), index="a3"),
        ],
        bindings=[
            binding("binding:start", "shape:arrow", "shape:api", "start"),
            binding("binding:end", "shape:arrow", "shape:db", "end"),
            binding("binding:lost", "shape:arrow", "shape:outside", "end"),
        ],
    )

    plan = sut.place_shapes(saved, AUTO, 1)

    placed = by_id(plan.records)
    shapes = {placed[i]["type"] + str(placed[i]["x"]): i for i in plan.root_shape_ids}
    bindings = [record for record in plan.records if record["typeName"] == "binding"]
    assert len(bindings) == 2
    assert all(record["id"].startswith("binding:n") for record in bindings)
    assert {(b["fromId"], b["toId"], b["props"]["terminal"]) for b in bindings} == {
        (shapes["arrow280.0"], shapes["geo180.0"], "start"),
        (shapes["arrow280.0"], shapes["geo480.0"], "end"),
    }


def test_should_copy_assets_with_new_ids_and_reuse_identical_ones() -> None:
    sut = make_sut(image_asset("asset:there", DATA_URL))
    saved = content(
        [
            shape("shape:a", "image", w=64, h=32, assetId="asset:same"),
            shape("shape:b", "image", w=64, h=32, assetId="asset:new", index="a2"),
            shape("shape:c", "image", w=64, h=32, assetId=None, index="a3"),
        ],
        assets=[
            image_asset("asset:same", DATA_URL),
            image_asset("asset:new", "data:image/png;base64,BBBB"),
        ],
    )

    plan = sut.place_shapes(saved, AUTO, 1)

    assets = [record for record in plan.records if record["typeName"] == "asset"]
    shapes = {
        record["props"]["assetId"] for record in plan.records if record["typeName"] == "shape"
    }
    assert [asset["props"]["src"] for asset in assets] == ["data:image/png;base64,BBBB"]
    assert assets[0]["id"].startswith("asset:n")
    assert shapes == {"asset:there", assets[0]["id"], None}


def test_should_store_an_image_repeated_inside_the_item_once() -> None:
    saved = content(
        [
            shape("shape:a", "image", w=64, h=32, assetId="asset:first"),
            shape("shape:b", "image", w=64, h=32, assetId="asset:again", index="a2"),
        ],
        assets=[image_asset("asset:first", DATA_URL), image_asset("asset:again", DATA_URL)],
    )

    plan = make_sut().place_shapes(saved, AUTO, 1)

    assets = [record for record in plan.records if record["typeName"] == "asset"]
    shapes = [record for record in plan.records if record["typeName"] == "shape"]
    assert len(assets) == 1
    assert {placed["props"]["assetId"] for placed in shapes} == {assets[0]["id"]}


def test_should_ignore_canvas_assets_without_readable_props() -> None:
    broken = {"id": "asset:broken", "typeName": "asset", "type": "image", "props": "src"}
    sut = make_sut(broken, image_asset("asset:there", DATA_URL))
    saved = content(
        [shape("shape:a", "image", w=1, h=1, assetId="asset:x")],
        assets=[image_asset("asset:x", DATA_URL)],
    )

    plan = sut.place_shapes(saved, AUTO, 1)

    assert [record["typeName"] for record in plan.records] == ["shape"]
    assert plan.records[0]["props"]["assetId"] == "asset:there"


# Mapping parents to children once per insertion keeps it linear in the number of shapes.
def test_should_map_the_saved_shapes_to_their_parents_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []
    original = canvas_geometry.children_by_parent

    def counted(records: Any) -> dict[str, list[dict[str, Any]]]:
        calls.append(1)
        return original(records)

    monkeypatch.setattr(canvas_insertion, "children_by_parent", counted)
    roots = [geo(f"shape:r{number}", number * 10, 0, index=f"a{number}") for number in range(1, 9)]

    plan = make_sut().place_shapes(content(roots), GalleryPlacement(x=0, y=0), 1)

    assert len(plan.root_shape_ids) == 8
    assert len(calls) == 1


def test_should_not_reuse_assets_without_a_source() -> None:
    sut = make_sut(image_asset("asset:there", ""))
    saved = content(
        [shape("shape:a", "image", w=1, h=1, assetId="asset:x")],
        assets=[image_asset("asset:x", "")],
    )

    plan = sut.place_shapes(saved, AUTO, 1)

    assert [record["typeName"] for record in plan.records] == ["asset", "shape"]


def test_should_stack_roots_above_existing_shapes_in_their_saved_order(
    sut: CanvasInsertion,
) -> None:
    saved = content([geo("shape:top", index="a9"), geo("shape:bottom", index="a2")])

    plan = sut.place_shapes(saved, AUTO, 1)

    placed = {record["id"]: record["index"] for record in plan.records}
    assert plan.root_shape_ids == ["shape:n2", "shape:n1"]
    assert placed == {"shape:n2": "a501", "shape:n1": "a502"}


def test_should_keep_shapes_whose_parent_was_not_saved(sut: CanvasInsertion) -> None:
    saved = content(
        [geo("shape:a", 10, 10), geo("shape:orphan", 50, 50, parent="shape:gone")],
        roots=["shape:a"],
    )

    plan = sut.place_shapes(saved, GalleryPlacement(x=0, y=0), 1)

    assert all(record["parentId"] == PAGE_ID for record in plan.records)
    assert len(plan.root_shape_ids) == 2


def test_should_fill_in_missing_shape_fields(sut: CanvasInsertion) -> None:
    bare = {
        "id": "shape:a",
        "type": "geo",
        "parentId": PAGE_ID,
        "x": "nan",
        "props": {"w": 10, "h": 10},
    }
    plan = sut.place_shapes(content([bare]), GalleryPlacement(x=5, y=5), 1)

    placed = plan.records[0]
    assert (placed["rotation"], placed["isLocked"], placed["opacity"], placed["meta"]) == (
        0,
        False,
        1,
        {},
    )
    assert (placed["x"], placed["y"]) == (5, 5)


@pytest.mark.parametrize(
    ("side", "corner"),
    [
        (PlacementSide.RIGHT, (180, 0)),
        (PlacementSide.LEFT, (-120, 0)),
        (PlacementSide.BELOW, (0, 130)),
        (PlacementSide.ABOVE, (0, -100)),
    ],
)
def test_should_place_next_to_a_shape(
    sut: CanvasInsertion, side: PlacementSide, corner: tuple[float, float]
) -> None:
    saved = content([geo("shape:a", 0, 0, 40, 20)])

    plan = sut.place_shapes(saved, GalleryPlacement(near_shape_id="shape:existing", side=side), 1)

    assert (plan.bounds.min_x, plan.bounds.min_y) == corner


def test_should_place_next_to_a_nested_shape_in_page_coordinates() -> None:
    sut = make_sut(
        group("shape:g", 1000, 1000), geo("shape:inner", 10, 10, 50, 50, parent="shape:g")
    )

    plan = sut.place_shapes(
        content([geo("shape:a")]), GalleryPlacement(near_shape_id="shape:inner", gap=0), 1
    )

    assert (plan.bounds.min_x, plan.bounds.min_y) == (1060, 1010)


@pytest.mark.parametrize("missing", ["shape:nope", PAGE_ID])
def test_should_refuse_to_place_next_to_something_that_is_not_a_shape(
    sut: CanvasInsertion, missing: str
) -> None:
    with pytest.raises(InvalidInputError, match="is not a shape in this diagram"):
        sut.place_shapes(content([geo("shape:a")]), GalleryPlacement(near_shape_id=missing), 1)


@pytest.mark.parametrize(
    ("placement", "message"),
    [
        (GalleryPlacement(x=1, near_shape_id="shape:existing"), "not both"),
        (GalleryPlacement(y=1, near_shape_id="shape:existing"), "not both"),
        (GalleryPlacement(x=1), "both x and y"),
        (GalleryPlacement(y=1), "both x and y"),
    ],
)
def test_should_refuse_ambiguous_placements(
    sut: CanvasInsertion, placement: GalleryPlacement, message: str
) -> None:
    with pytest.raises(InvalidInputError, match=message):
        sut.place_shapes(content([geo("shape:a")]), placement, 1)


@pytest.mark.parametrize(
    "shapes",
    [
        None,
        [],
        ["text"],
        [{"id": "shape:a", "type": "geo"}],
        [{"id": "binding:a", "type": "geo", "props": {}}],
        [{"id": 7, "type": "geo", "props": {}}],
        [{"id": "shape:a", "type": None, "props": {}}],
    ],
)
def test_should_refuse_invalid_content(sut: CanvasInsertion, shapes: object) -> None:
    with pytest.raises(InvalidInputError, match="invalid shapes"):
        sut.place_shapes({"schema": SCHEMA, "shapes": shapes}, AUTO, 1)


def test_should_refuse_shapes_saved_twice(sut: CanvasInsertion) -> None:
    saved = content([geo("shape:a", 0, 0), geo("shape:a", 50, 50, index="a2")])
    with pytest.raises(InvalidInputError, match="invalid shapes"):
        sut.place_shapes(saved, AUTO, 1)


def test_should_refuse_shapes_whose_parents_loop(sut: CanvasInsertion) -> None:
    saved = content(
        [
            geo("shape:root"),
            group("shape:a") | {"parentId": "shape:b"},
            group("shape:b") | {"parentId": "shape:a"},
        ],
        roots=["shape:root"],
    )
    with pytest.raises(InvalidInputError, match="invalid shapes"):
        sut.place_shapes(saved, AUTO, 1)


def test_should_accept_roots_saved_inside_another_saved_shape(sut: CanvasInsertion) -> None:
    saved = content(
        [group("shape:g"), geo("shape:a", parent="shape:g")], roots=["shape:g", "shape:a"]
    )

    plan = sut.place_shapes(saved, GalleryPlacement(x=0, y=0), 1)

    assert len(plan.root_shape_ids) == 2
    assert all(record["parentId"] == PAGE_ID for record in plan.records)


def test_should_place_next_to_a_group_in_a_broken_loop() -> None:
    sut = make_sut(
        group("shape:a", 0, 0) | {"parentId": "shape:b"},
        group("shape:b", 0, 0) | {"parentId": "shape:a"},
    )

    plan = sut.place_shapes(
        content([geo("shape:x")]), GalleryPlacement(near_shape_id="shape:a", gap=0), 1
    )

    assert plan.bounds.min_x == 100


def test_should_refuse_content_from_another_editor_version(sut: CanvasInsertion) -> None:
    saved = content([geo("shape:a")]) | {
        "schema": {"schemaVersion": 2, "sequences": {"com.tldraw.shape": 3}}
    }
    with pytest.raises(InvalidInputError, match="another version of the editor"):
        sut.place_shapes(saved, AUTO, 1)


def test_should_skip_generated_ids_already_in_the_canvas() -> None:
    ids = iter(["existing", "existing", "fresh", "fresh", "other"])
    sut = CanvasInsertion(canvas(geo("shape:existing")), lambda: next(ids))

    plan = sut.place_shapes(content([geo("shape:a"), geo("shape:b", index="a2")]), AUTO, 1)

    assert plan.created_ids == ["shape:fresh", "shape:other"]


def test_should_give_up_when_ids_keep_colliding() -> None:
    sut = CanvasInsertion(canvas(geo("shape:same")), lambda: "same")
    with pytest.raises(ConflictError):
        sut.place_shapes(content([geo("shape:a")]), AUTO, 1)


def test_should_refuse_more_new_shapes_than_indexes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(canvas_insertion, "indexes_above", lambda top: iter([f"{top}01"]))
    with pytest.raises(InvalidInputError, match="too many shapes"):
        make_sut().place_shapes(content([geo("shape:a"), geo("shape:b")]), AUTO, 1)


def test_should_only_stack_above_shapes_on_the_page_itself() -> None:
    sut = make_sut(
        group("shape:g", index="a3"),
        geo("shape:child", parent="shape:g", index="zz"),
        geo("shape:x") | {"index": 7},
    )
    plan = sut.place_shapes(content([geo("shape:a")]), AUTO, 1)
    assert plan.records[0]["index"] == "a301"


def test_should_count_the_shapes_already_in_the_canvas(sut: CanvasInsertion) -> None:
    assert sut.shape_count() == 1
    assert make_sut().shape_count() == 0


def test_should_insert_an_image_as_an_embedded_asset_and_an_image_shape(
    sut: CanvasInsertion,
) -> None:
    data = png(64, 32)

    plan = sut.place_image(
        data, ImageMimeType.PNG, "Logo", (64, 32), GalleryPlacement(x=10, y=20), 2
    )

    asset, image = plan.records
    assert asset == {
        "id": "asset:n1",
        "typeName": "asset",
        "type": "image",
        "props": {
            "name": "Logo",
            "src": "data:image/png;base64," + base64.b64encode(data).decode(),
            "w": 64,
            "h": 32,
            "mimeType": "image/png",
            "isAnimated": False,
            "fileSize": len(data),
        },
        "meta": {},
    }
    assert image == {
        "id": "shape:n2",
        "typeName": "shape",
        "type": "image",
        "x": 10,
        "y": 20,
        "rotation": 0,
        "isLocked": False,
        "opacity": 1,
        "meta": {},
        "parentId": PAGE_ID,
        "index": "a501",
        "props": {
            "w": 128,
            "h": 64,
            "playing": True,
            "url": "",
            "assetId": "asset:n1",
            "crop": None,
            "flipX": False,
            "flipY": False,
            "altText": "",
        },
    }
    assert plan.root_shape_ids == ["shape:n2"]
    assert plan.bounds == Bounds(10, 20, 138, 84)


def test_should_reuse_an_image_already_in_the_diagram() -> None:
    data = b"GIF89a"
    src = "data:image/gif;base64," + base64.b64encode(data).decode()
    sut = make_sut(image_asset("asset:there", src))

    plan = sut.place_image(data, ImageMimeType.GIF, "Spinner", (10, 10), AUTO, 1)

    assert [record["typeName"] for record in plan.records] == ["shape"]
    assert plan.records[0]["props"]["assetId"] == "asset:there"


def test_should_mark_gifs_as_animated(sut: CanvasInsertion) -> None:
    plan = sut.place_image(b"GIF89a", ImageMimeType.GIF, "Spinner", (10, 10), AUTO, 1)
    assert plan.records[0]["props"]["isAnimated"] is True


def test_should_place_an_image_next_to_a_shape(sut: CanvasInsertion) -> None:
    plan = sut.place_image(
        png(10, 10),
        ImageMimeType.PNG,
        "Logo",
        (10, 10),
        GalleryPlacement(near_shape_id="shape:existing", side=PlacementSide.ABOVE, gap=5),
        1,
    )
    assert plan.bounds == Bounds(0, -15, 10, -5)


def test_should_refuse_images_on_a_canvas_from_another_editor_version() -> None:
    schema = {"schemaVersion": 2, "sequences": {**SCHEMA["sequences"], "com.tldraw.shape.image": 6}}
    sut = CanvasInsertion(canvas(schema=schema), sequential_ids())
    with pytest.raises(InvalidInputError, match="com.tldraw.shape.image"):
        sut.place_image(png(1, 1), ImageMimeType.PNG, "Logo", (1, 1), AUTO, 1)
