import json
import uuid
from itertools import count
from typing import Any, cast
from unittest.mock import AsyncMock, create_autospec

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
from tests.tldraw_records import PAGE_ID, arrow, binding, canvas, content, geo, png

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
def items() -> GalleryItemRepository:
    mock = cast(GalleryItemRepository, create_autospec(GalleryItemRepository))
    mock.get_by_id = AsyncMock(return_value=shapes_item())  # type: ignore[method-assign]
    return mock


@pytest.fixture
def diagrams(diagram: Diagram) -> DiagramRepository:
    mock = cast(DiagramRepository, create_autospec(DiagramRepository))
    mock.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    mock.update = AsyncMock(side_effect=lambda updated: updated)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def notifier() -> DiagramUpdateNotifier:
    return cast(DiagramUpdateNotifier, create_autospec(DiagramUpdateNotifier))


@pytest.fixture
def recorder() -> RevisionRecorder:
    return cast(RevisionRecorder, create_autospec(RevisionRecorder))


@pytest.fixture
def sut(
    items: GalleryItemRepository,
    diagrams: DiagramRepository,
    notifier: DiagramUpdateNotifier,
    recorder: RevisionRecorder,
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
    sut: InsertGalleryItem, diagram: Diagram, diagrams: DiagramRepository
) -> None:
    before = json.loads(json.dumps(diagram.canvas_state))

    inserted = await sut.execute(params(diagram))

    store = inserted.diagram.canvas_state["store"]  # type: ignore[index]
    assert set(store) == set(before["store"]) | {"shape:n1"}
    assert store["shape:api"] == before["store"]["shape:api"]
    assert (store["shape:n1"]["x"], store["shape:n1"]["y"], store["shape:n1"]["parentId"]) == (
        180,
        0,
        PAGE_ID,
    )
    assert inserted.diagram.canvas_state["schema"] == before["schema"]  # type: ignore[index]
    assert (inserted.created_ids, inserted.root_shape_ids) == (["shape:n1"], ["shape:n1"])
    assert (inserted.x, inserted.y, inserted.width, inserted.height) == (180, 0, 120, 60)
    diagrams.update.assert_awaited_once()  # type: ignore[attr-defined]


async def test_should_record_the_change_under_its_author_and_notify_every_editor(
    sut: InsertGalleryItem,
    diagram: Diagram,
    recorder: RevisionRecorder,
    notifier: DiagramUpdateNotifier,
) -> None:
    before = DiagramSnapshot.of(diagram)

    inserted = await sut.execute(params(diagram))

    recorder.record.assert_awaited_once_with(  # type: ignore[attr-defined]
        diagram.id,
        before,
        DiagramSnapshot.of(inserted.diagram),
        AGENT,
        summary="Inserted “Queue” from the gallery",
    )
    notifier.notify_updated.assert_awaited_once_with(inserted.diagram, None)  # type: ignore[attr-defined]


async def test_should_use_and_cut_the_given_summary(
    sut: InsertGalleryItem, diagram: Diagram, recorder: RevisionRecorder
) -> None:
    await sut.execute(params(diagram, revision_summary="x" * 600))

    assert recorder.record.await_args.kwargs["summary"] == "x" * 500  # type: ignore[attr-defined]


async def test_should_insert_twice_as_two_copies(sut: InsertGalleryItem, diagram: Diagram) -> None:
    first = await sut.execute(params(diagram))
    second = await sut.execute(params(diagram))

    store = second.diagram.canvas_state["store"]  # type: ignore[index]
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
    sut: InsertGalleryItem, diagram: Diagram, items: GalleryItemRepository
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
    items.get_by_id = AsyncMock(return_value=shapes_item(saved))  # type: ignore[method-assign]

    inserted = await sut.execute(params(diagram))

    store = inserted.diagram.canvas_state["store"]  # type: ignore[index]
    bindings = [store[i] for i in inserted.created_ids if store[i]["typeName"] == "binding"]
    assert len(inserted.created_ids) == 5
    assert all(
        b["fromId"] in inserted.root_shape_ids and b["toId"] in inserted.root_shape_ids
        for b in bindings
    )


async def test_should_insert_an_image(
    sut: InsertGalleryItem, diagram: Diagram, items: GalleryItemRepository
) -> None:
    items.get_by_id = AsyncMock(return_value=image_item(png(64, 32)))  # type: ignore[method-assign]

    inserted = await sut.execute(params(diagram, x=0, y=200, scale=2))

    store = inserted.diagram.canvas_state["store"]  # type: ignore[index]
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
    items: GalleryItemRepository,
    diagrams: DiagramRepository,
) -> None:
    items.get_by_id = AsyncMock(return_value=image_item(b"\x89PNG\r\n\x1a\n"))  # type: ignore[method-assign]

    with pytest.raises(InvalidInputError, match="size of this image"):
        await sut.execute(params(diagram))
    diagrams.update.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize("stored", FOREIGN_ITEMS)
async def test_should_not_insert_items_of_other_owners(
    sut: InsertGalleryItem,
    diagram: Diagram,
    items: GalleryItemRepository,
    diagrams: DiagramRepository,
    stored: GalleryItem | None,
) -> None:
    items.get_by_id = AsyncMock(return_value=stored)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError, match="Gallery item"):
        await sut.execute(params(diagram))
    diagrams.get_by_id.assert_not_awaited()  # type: ignore[attr-defined]


async def test_should_raise_not_found_for_a_missing_diagram(
    sut: InsertGalleryItem, diagram: Diagram, diagrams: DiagramRepository
) -> None:
    diagrams.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError, match=f"Diagram {diagram.id}"):
        await sut.execute(params(diagram))


@pytest.mark.parametrize("canvas_state", [None, {}, {"store": {}}])
async def test_should_need_a_canvas_opened_in_the_editor(
    sut: InsertGalleryItem,
    diagram: Diagram,
    diagrams: DiagramRepository,
    canvas_state: dict[str, Any] | None,
) -> None:
    diagram.canvas_state = canvas_state

    with pytest.raises(InvalidInputError, match="no canvas yet"):
        await sut.execute(params(diagram))
    diagrams.update.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize("scale", [0.09, 10.01])
async def test_should_refuse_a_scale_out_of_bounds(
    sut: InsertGalleryItem, diagram: Diagram, items: GalleryItemRepository, scale: float
) -> None:
    with pytest.raises(InvalidInputError, match="between 0.1 and 10"):
        await sut.execute(params(diagram, scale=scale))
    items.get_by_id.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize("scale", [0.1, 10])
async def test_should_accept_the_scale_bounds(
    sut: InsertGalleryItem, diagram: Diagram, scale: float
) -> None:
    inserted = await sut.execute(params(diagram, scale=scale))
    assert inserted.width == 120 * scale


async def test_should_refuse_to_go_over_the_shapes_per_page(
    sut: InsertGalleryItem,
    diagram: Diagram,
    diagrams: DiagramRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(insert_gallery_item, "CANVAS_MAX_SHAPES_PER_PAGE", 3)
    diagram.canvas_state = canvas(geo("shape:1"), geo("shape:2"))
    await sut.execute(params(diagram))

    with pytest.raises(InvalidInputError, match="more than 3 shapes"):
        await sut.execute(params(diagram))
    assert diagrams.update.await_count == 1  # type: ignore[attr-defined]


async def test_should_refuse_to_grow_the_canvas_over_the_limit(
    items: GalleryItemRepository,
    diagrams: DiagramRepository,
    notifier: DiagramUpdateNotifier,
    recorder: RevisionRecorder,
    diagram: Diagram,
) -> None:
    items.get_by_id = AsyncMock(return_value=image_item(png(64, 32)))  # type: ignore[method-assign]
    size = len(json.dumps(diagram.canvas_state).encode())
    sut = InsertGalleryItem(
        items, diagrams, notifier, recorder, GalleryLimits(1, 1, max_canvas_bytes=size + 100)
    )

    with pytest.raises(PayloadTooLargeError, match=f"limit {size + 100}"):
        await sut.execute(params(diagram))
    diagrams.update.assert_not_awaited()  # type: ignore[attr-defined]
    notifier.notify_updated.assert_not_awaited()  # type: ignore[attr-defined]


async def test_should_allow_a_canvas_exactly_at_the_limit(
    items: GalleryItemRepository,
    diagrams: DiagramRepository,
    notifier: DiagramUpdateNotifier,
    recorder: RevisionRecorder,
    diagram: Diagram,
) -> None:
    probe = InsertGalleryItem(items, diagrams, notifier, recorder, LIMITS, lambda: "fixed")
    copy = diagram.model_copy(deep=True)
    diagrams.get_by_id = AsyncMock(return_value=copy)  # type: ignore[method-assign]
    size = len(json.dumps((await probe.execute(params(diagram))).diagram.canvas_state).encode())
    diagrams.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    sut = InsertGalleryItem(
        items,
        diagrams,
        notifier,
        recorder,
        GalleryLimits(1, 1, max_canvas_bytes=size),
        lambda: "fixed",
    )

    await sut.execute(params(diagram))
