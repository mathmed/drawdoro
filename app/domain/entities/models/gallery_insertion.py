import uuid

from app.domain.entities.models.base_model import BaseModel
from app.domain.entities.models.diagram import Diagram


# What inserting a gallery item into a diagram created, and where it landed.
class GalleryInsertion(BaseModel):
    diagram: Diagram
    item_id: uuid.UUID
    # Every record added to the canvas: shapes, bindings and assets.
    created_ids: list[str]
    # The top-level shapes of the inserted copy, to select, move or connect it.
    root_shape_ids: list[str]
    x: float
    y: float
    width: float
    height: float
