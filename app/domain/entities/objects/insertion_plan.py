from dataclasses import dataclass
from typing import Any

from app.domain.entities.objects.bounds import Bounds


# The records to add to a canvas for one inserted gallery item, and where they land.
@dataclass(frozen=True)
class InsertionPlan:
    records: list[dict[str, Any]]
    root_shape_ids: list[str]
    bounds: Bounds

    @property
    def created_ids(self) -> list[str]:
        return [str(record["id"]) for record in self.records]
