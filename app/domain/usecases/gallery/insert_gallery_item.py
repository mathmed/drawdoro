import json
import uuid
from collections.abc import Callable
from typing import Any

from app.domain.constants.canvas import (
    CANVAS_DEFAULT_GAP,
    CANVAS_MAX_SCALE,
    CANVAS_MAX_SHAPES_PER_PAGE,
    CANVAS_MIN_SCALE,
)
from app.domain.constants.revisions import REVISION_SUMMARY_MAX_LENGTH
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.gallery_insertion import GalleryInsertion
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.entities.objects.gallery_placement import GalleryPlacement
from app.domain.entities.objects.insertion_plan import InsertionPlan
from app.domain.enums.placement_side import PlacementSide
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError, PayloadTooLargeError
from app.domain.services.canvas_insertion import CanvasInsertion
from app.domain.services.gallery_ownership import get_owned_gallery_item
from app.domain.services.image_size import read_image_size
from app.domain.services.revision_recorder import RevisionRecorder


class InsertGalleryItemParams(InputData):
    diagram_id: uuid.UUID
    item_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    # Top-left corner of the inserted copy in page coordinates; or next to near_shape_id.
    x: float | None = None
    y: float | None = None
    near_shape_id: str | None = None
    side: PlacementSide = PlacementSide.RIGHT
    gap: float = CANVAS_DEFAULT_GAP
    scale: float = 1
    author: RevisionAuthor = RevisionAuthor()
    revision_summary: str | None = None


def _random_id() -> str:
    return uuid.uuid4().hex


# Copies one of the caller's gallery items into a diagram's canvas, the server-side twin of the
# editor's Gallery panel: the item keeps its layout, gets new ids and lands where asked without
# covering anything. The change is saved like any other edit: recorded in the history under its
# author and pushed to the editors that have the diagram open.
class InsertGalleryItem(Usecase[InsertGalleryItemParams, GalleryInsertion]):
    def __init__(
        self,
        items: GalleryItemRepository,
        diagrams: DiagramRepository,
        notifier: DiagramUpdateNotifier,
        recorder: RevisionRecorder,
        limits: GalleryLimits,
        new_id: Callable[[], str] = _random_id,
    ) -> None:
        self._items = items
        self._diagrams = diagrams
        self._notifier = notifier
        self._recorder = recorder
        self._limits = limits
        self._new_id = new_id

    async def execute(self, params: InsertGalleryItemParams) -> GalleryInsertion:
        if not CANVAS_MIN_SCALE <= params.scale <= CANVAS_MAX_SCALE:
            raise InvalidInputError(
                f"The scale must be between {CANVAS_MIN_SCALE} and {CANVAS_MAX_SCALE}"
            )
        item = await get_owned_gallery_item(self._items, params.item_id, params.owner_id)
        diagram = await self._diagrams.get_by_id(params.diagram_id)
        if diagram is None:
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        canvas = diagram.canvas_state
        if not canvas or "schema" not in canvas:
            raise InvalidInputError(
                "The diagram has no canvas yet: open it once in the editor, then insert again"
            )
        insertion = CanvasInsertion(canvas, self._new_id)
        plan = _plan(insertion, item, params)
        merged = self._merged_canvas(canvas, insertion, plan)
        updated = await self._save(diagram, merged, params, item)
        return GalleryInsertion(
            diagram=updated,
            item_id=item.id,
            created_ids=plan.created_ids,
            root_shape_ids=plan.root_shape_ids,
            x=round(plan.bounds.min_x, 2),
            y=round(plan.bounds.min_y, 2),
            width=round(plan.bounds.width, 2),
            height=round(plan.bounds.height, 2),
        )

    def _merged_canvas(
        self, canvas: dict[str, Any], insertion: CanvasInsertion, plan: InsertionPlan
    ) -> dict[str, Any]:
        _ensure_room_for(insertion, plan)
        store = dict(canvas.get("store") or {})
        store.update({str(record["id"]): record for record in plan.records})
        merged = canvas | {"store": store}
        self._ensure_fits(merged)
        return merged

    def _ensure_fits(self, canvas: dict[str, Any]) -> None:
        size = len(json.dumps(canvas).encode())
        if size > self._limits.max_canvas_bytes:
            raise PayloadTooLargeError(
                f"The diagram would grow to {size} bytes (limit {self._limits.max_canvas_bytes})"
            )

    async def _save(
        self,
        diagram: Diagram,
        canvas: dict[str, Any],
        params: InsertGalleryItemParams,
        item: GalleryItem,
    ) -> Diagram:
        before = DiagramSnapshot.of(diagram)
        diagram.canvas_state = canvas
        updated = await self._diagrams.update(diagram)
        summary = params.revision_summary or f"Inserted “{item.name}” from the gallery"
        await self._recorder.record(
            updated.id,
            before,
            DiagramSnapshot.of(updated),
            params.author,
            summary=summary[:REVISION_SUMMARY_MAX_LENGTH],
        )
        # No origin tab: every open editor, the requester's included, must load the new shapes.
        await self._notifier.notify_updated(updated, None)
        return updated


def _plan(
    insertion: CanvasInsertion, item: GalleryItem, params: InsertGalleryItemParams
) -> InsertionPlan:
    placement = GalleryPlacement(
        x=params.x,
        y=params.y,
        near_shape_id=params.near_shape_id,
        side=params.side,
        gap=params.gap,
    )
    if item.image_data is None or item.image_mime_type is None:
        return insertion.place_shapes(item.content or {}, placement, params.scale)
    size = read_image_size(item.image_data, item.image_mime_type)
    if size is None:
        raise InvalidInputError("The size of this image can't be read, so it can't be inserted")
    return insertion.place_image(
        item.image_data, item.image_mime_type, item.name, size, placement, params.scale
    )


def _ensure_room_for(insertion: CanvasInsertion, plan: InsertionPlan) -> None:
    new_shapes = sum(1 for record in plan.records if record["typeName"] == "shape")
    if insertion.shape_count() + new_shapes > CANVAS_MAX_SHAPES_PER_PAGE:
        raise InvalidInputError(
            f"The diagram would have more than {CANVAS_MAX_SHAPES_PER_PAGE} shapes"
        )
