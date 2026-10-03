import json
import uuid
from itertools import count
from typing import Any
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.placement_side import PlacementSide
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError, PayloadTooLargeError
from app.domain.services.revision_recorder import RevisionRecorder
from app.domain.usecases.gallery import insert_gallery_item
from app.domain.usecases.gallery.insert_gallery_item import (
    InsertGalleryItem,
    InsertGalleryItemParams,
)
from tests.doubles import double
from tests.tldraw_records import (
    PAGE_ID,
    arrow,
    binding,
    canvas,
    content,
    geo,
    png,
    saved_canvas,
)

from .conftest import FOREIGN_ITEMS, OWNER_ID

AGENT = RevisionAuthor(user_id=OWNER_ID, origin=RevisionOrigin.AGENT, agent_name="Claude")
LIMITS = GalleryLimits(max_image_bytes=1_000_000, max_shapes_bytes=1_000_000)


def shapes_item(saved: dict[str, Any] | None = None) -> GalleryItem:
    return GalleryItem(
        owner_id=OWNER_ID,
        name="Queue",
        kind=GalleryItemKind.SHAPES,
        content=saved or content([geo("shape:q", 0, 0, 120, 60)]),
    )


def image_item(data: bytes) -> GalleryItem:
    return GalleryItem(
        owner_id=OWNER_ID,
        name="Logo",
        kind=GalleryItemKind.IMAGE,
        image_data=data,
        image_mime_type=ImageMimeType.PNG,
    )


@pytest.fixture
def diagram() -> Diagram:
    return Diagram(
        project_id=uuid.uuid4(),
        name="Checkout",
        canvas_state=canvas(geo("shape:api", 0, 0, 100, 50)),
    )


@pytest.fixture
def items() -> NonCallableMagicMock:
    mock = double(GalleryItemRepository)
    mock.get_by_id.return_value = shapes_item()
    return mock


@pytest.fixture
def diagrams(diagram: Diagram) -> NonCallableMagicMock:
    mock = double(DiagramRepository)
    mock.get_by_id.return_value = diagram
    mock.update.side_effect = lambda updated: updated
    return mock


@pytest.fixture
def notifier() -> NonCallableMagicMock:
    return double(DiagramUpdateNotifier)


@pytest.fixture
def recorder() -> NonCallableMagicMock:
    return double(RevisionRecorder)


@pytest.fixture
def sut(
    items: NonCallableMagicMock,
    diagrams: NonCallableMagicMock,
    notifier: NonCallableMagicMock,
    recorder: NonCallableMagicMock,
) -> InsertGalleryItem:
    numbers = count(1)
    return InsertGalleryItem(
        items, diagrams, notifier, recorder, LIMITS, lambda: f"n{next(numbers)}"
    )


def params(diagram: Diagram, **values: Any) -> InsertGalleryItemParams:
    return InsertGalleryItemParams(
        diagram_id=diagram.id, item_id=uuid.uuid4(), owner_id=OWNER_ID, author=AGENT, **values
    )


async def test_should_add_the_item_to_the_canvas_and_report_where(
    sut: InsertGalleryItem, diagram: Diagram, diagrams: NonCallableMagicMock
) -> None:
    before = json.loads(json.dumps(diagram.canvas_state))

    inserted = await sut.execute(params(diagram))

    store = saved_canvas(inserted.diagram)["store"]
    assert set(store) == set(before["store"]) | {"shape:n1"}
    assert store["shape:api"] == before["store"]["shape:api"]
    assert (store["shape:n1"]["x"], store["shape:n1"]["y"], store["shape:n1"]["parentId"]) == (
        180,
        0,
        PAGE_ID,
    )
    assert saved_canvas(inserted.diagram)["schema"] == before["schema"]
    assert (inserted.created_ids, inserted.root_shape_ids) == (["shape:n1"], ["shape:n1"])
    assert (inserted.x, inserted.y, inserted.width, inserted.height) == (180, 0, 120, 60)
    diagrams.update.assert_awaited_once()


# Ownership is checked on the item that was loaded, so it must be the one asked for.
async def test_should_load_the_requested_item_and_diagram(
    sut: InsertGalleryItem,
    diagram: Diagram,
    items: NonCallableMagicMock,
    diagrams: NonCallableMagicMock,
) -> None:
    request = params(diagram)

    await sut.execute(request)

    items.get_by_id.assert_awaited_once_with(request.item_id)
    diagrams.get_by_id.assert_awaited_once_with(diagram.id)


async def test_should_round_the_reported_position_and_size(
    sut: InsertGalleryItem, diagram: Diagram, items: NonCallableMagicMock
) -> None:
    saved = content([geo("shape:q", 0, 0, 10, 10)])
    items.get_by_id.return_value = shapes_item(saved)

    inserted = await sut.execute(params(diagram, x=1.23456, y=6.54321, scale=1.23456))

    assert (inserted.x, inserted.y, inserted.width, inserted.height) == (1.23, 6.54, 12.35, 12.35)


# Only an image with its type is inserted as an image; stray bytes on a shapes item are ignored.
async def test_should_insert_an_item_without_image_type_as_shapes(
    sut: InsertGalleryItem, diagram: Diagram, items: NonCallableMagicMock
) -> None:
    stray = shapes_item().model_copy(update={"image_data": b"not an image"})
    items.get_by_id.return_value = stray

    inserted = await sut.execute(params(diagram))

    assert inserted.created_ids == ["shape:n1"]


async def test_should_record_the_change_under_its_author_and_notify_every_editor(
    sut: InsertGalleryItem,
    diagram: Diagram,
    recorder: NonCallableMagicMock,
    notifier: NonCallableMagicMock,
) -> None:
    before = DiagramSnapshot.of(diagram)

    inserted = await sut.execute(params(diagram))

    recorder.record.assert_awaited_once_with(
        diagram.id,
        before,
        DiagramSnapshot.of(inserted.diagram),
        AGENT,
        summary="Inserted “Queue” from the gallery",
    )
    notifier.notify_updated.assert_awaited_once_with(inserted.diagram, None)


async def test_should_use_and_cut_the_given_summary(
    sut: InsertGalleryItem, diagram: Diagram, recorder: NonCallableMagicMock
) -> None:
    await sut.execute(params(diagram, revision_summary="x" * 600))

    assert recorder.record.await_args.kwargs["summary"] == "x" * 500


async def test_should_insert_twice_as_two_copies(sut: InsertGalleryItem, diagram: Diagram) -> None:
    first = await sut.execute(params(diagram))
    second = await sut.execute(params(diagram))

    store = saved_canvas(second.diagram)["store"]
    assert first.root_shape_ids != second.root_shape_ids
    assert {*first.created_ids, *second.created_ids} <= set(store)
    assert second.x == first.x + first.width + 80


async def test_should_pass_the_placement_and_scale(
    sut: InsertGalleryItem, diagram: Diagram
) -> None:
    inserted = await sut.execute(
        params(diagram, near_shape_id="shape:api", side=PlacementSide.BELOW, gap=20, scale=0.5)
    )
    assert (inserted.x, inserted.y, inserted.width, inserted.height) == (0, 70, 60, 30)

    at_point = await sut.execute(params(diagram, x=-10.123, y=5))
    assert (at_point.x, at_point.y) == (-10.12, 5)


async def test_should_insert_connected_shapes(
    sut: InsertGalleryItem, diagram: Diagram, items: NonCallableMagicMock
) -> None:
    saved = content(
        [
            geo("shape:a", index="a1"),
            geo("shape:b", 300, 0, index="a2"),
            arrow("shape:arrow", 100, 25, (200, 0), index="a3"),
        ],
        bindings=[
            binding("binding:1", "shape:arrow", "shape:a", "start"),
            binding("binding:2", "shape:arrow", "shape:b", "end"),
        ],
    )
    items.get_by_id.return_value = shapes_item(saved)

    inserted = await sut.execute(params(diagram))

    store = saved_canvas(inserted.diagram)["store"]
    bindings = [store[i] for i in inserted.created_ids if store[i]["typeName"] == "binding"]
    assert len(inserted.created_ids) == 5
    assert all(
        b["fromId"] in inserted.root_shape_ids and b["toId"] in inserted.root_shape_ids
        for b in bindings
    )


async def test_should_insert_an_image(
    sut: InsertGalleryItem, diagram: Diagram, items: NonCallableMagicMock
) -> None:
    items.get_by_id.return_value = image_item(png(64, 32))

    inserted = await sut.execute(params(diagram, x=0, y=200, scale=2))

    store = saved_canvas(inserted.diagram)["store"]
    asset, image = (store[record_id] for record_id in inserted.created_ids)
    assert asset["props"]["src"].startswith("data:image/png;base64,")
    assert (asset["props"]["w"], asset["props"]["h"], asset["props"]["name"]) == (64, 32, "Logo")
    assert (image["props"]["assetId"], image["props"]["w"], image["props"]["h"]) == (
        asset["id"],
        128,
        64,
    )
    assert (inserted.width, inserted.height) == (128, 64)


async def test_should_refuse_images_whose_size_cannot_be_read(
    sut: InsertGalleryItem,
    diagram: Diagram,
    items: NonCallableMagicMock,
    diagrams: NonCallableMagicMock,
) -> None:
    items.get_by_id.return_value = image_item(b"\x89PNG\r\n\x1a\n")

    with pytest.raises(InvalidInputError) as refused:
        await sut.execute(params(diagram))
    assert refused.value.message == (
        "The size of this image can't be read, so it can't be inserted"
    )
    diagrams.update.assert_not_awaited()


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_not_insert_items_of_other_owners(
    sut: InsertGalleryItem,
    diagram: Diagram,
    items: NonCallableMagicMock,
    diagrams: NonCallableMagicMock,
    stored: GalleryItem | None,
) -> None:
    items.get_by_id.return_value = stored

    with pytest.raises(NotFoundError, match="Gallery item"):
        await sut.execute(params(diagram))
    diagrams.get_by_id.assert_not_awaited()


async def test_should_raise_not_found_for_a_missing_diagram(
    sut: InsertGalleryItem, diagram: Diagram, diagrams: NonCallableMagicMock
) -> None:
    diagrams.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match=f"Diagram {diagram.id}"):
        await sut.execute(params(diagram))


@pytest.mark.parametrize("canvas_state", [None, {}, {"store": {}}])
async def test_should_need_a_canvas_opened_in_the_editor(
    sut: InsertGalleryItem,
    diagram: Diagram,
    diagrams: NonCallableMagicMock,
    canvas_state: dict[str, Any] | None,
) -> None:
    diagram.canvas_state = canvas_state

    with pytest.raises(InvalidInputError) as refused:
        await sut.execute(params(diagram))
    assert refused.value.message == (
        "The diagram has no canvas yet: open it once in the editor, then insert again"
    )
    diagrams.update.assert_not_awaited()


@pytest.mark.parametrize("scale", [0.09, 10.01])
async def test_should_refuse_a_scale_out_of_bounds(
    sut: InsertGalleryItem, diagram: Diagram, items: NonCallableMagicMock, scale: float
) -> None:
    with pytest.raises(InvalidInputError, match="between 0.1 and 10"):
        await sut.execute(params(diagram, scale=scale))
    items.get_by_id.assert_not_awaited()


@pytest.mark.parametrize("scale", [0.1, 10])
async def test_should_accept_the_scale_bounds(
    sut: InsertGalleryItem, diagram: Diagram, scale: float
) -> None:
    inserted = await sut.execute(params(diagram, scale=scale))
    assert inserted.width == 120 * scale


async def test_should_refuse_to_go_over_the_shapes_per_page(
    sut: InsertGalleryItem,
    diagram: Diagram,
    diagrams: NonCallableMagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(insert_gallery_item, "CANVAS_MAX_SHAPES_PER_PAGE", 3)
    diagram.canvas_state = canvas(geo("shape:1"), geo("shape:2"))
    await sut.execute(params(diagram))

    with pytest.raises(InvalidInputError, match="more than 3 shapes"):
        await sut.execute(params(diagram))
    assert diagrams.update.await_count == 1


async def test_should_refuse_to_grow_the_canvas_over_the_limit(
    items: NonCallableMagicMock,
    diagrams: NonCallableMagicMock,
    notifier: NonCallableMagicMock,
    recorder: NonCallableMagicMock,
    diagram: Diagram,
) -> None:
    items.get_by_id.return_value = image_item(png(64, 32))
    size = len(json.dumps(diagram.canvas_state).encode())
    sut = InsertGalleryItem(
        items, diagrams, notifier, recorder, GalleryLimits(1, 1, max_canvas_bytes=size + 100)
    )

    with pytest.raises(PayloadTooLargeError, match=f"limit {size + 100}"):
        await sut.execute(params(diagram))
    diagrams.update.assert_not_awaited()
    notifier.notify_updated.assert_not_awaited()


async def test_should_allow_a_canvas_exactly_at_the_limit(
    items: NonCallableMagicMock,
    diagrams: NonCallableMagicMock,
    notifier: NonCallableMagicMock,
    recorder: NonCallableMagicMock,
    diagram: Diagram,
) -> None:
    probe = InsertGalleryItem(items, diagrams, notifier, recorder, LIMITS, lambda: "fixed")
    copy = diagram.model_copy(deep=True)
    diagrams.get_by_id.return_value = copy
    size = len(json.dumps((await probe.execute(params(diagram))).diagram.canvas_state).encode())
    diagrams.get_by_id.return_value = diagram
    sut = InsertGalleryItem(
        items,
        diagrams,
        notifier,
        recorder,
        GalleryLimits(1, 1, max_canvas_bytes=size),
        lambda: "fixed",
    )

    await sut.execute(params(diagram))
