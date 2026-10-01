from dataclasses import dataclass

from app.domain.constants.canvas import CANVAS_DEFAULT_GAP
from app.domain.enums.placement_side import PlacementSide


# Where an inserted item goes, as the top-left corner of its bounds in page coordinates: at x/y,
# next to a shape (near_shape_id, on `side`, `gap` away), or, with neither, to the right of
# everything already on the page so nothing is covered.
@dataclass(frozen=True)
class GalleryPlacement:
    x: float | None = None
    y: float | None = None
    near_shape_id: str | None = None
    side: PlacementSide = PlacementSide.RIGHT
    gap: float = CANVAS_DEFAULT_GAP
