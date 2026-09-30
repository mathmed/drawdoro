from typing import Any

from pydantic import field_validator

from app.domain.entities.models.base_model import BaseModel
from app.domain.entities.models.diagram import Diagram


class DiagramSnapshot(BaseModel):
    name: str
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None

    # The editor saves {} where agents leave None; both mean "nothing", so neither makes a revision.
    @field_validator("canvas_state", "semantic_metadata")
    @classmethod
    def _empty_as_none(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return value or None

    @classmethod
    def of(cls, diagram: Diagram) -> DiagramSnapshot:
        return cls(
            name=diagram.name,
            canvas_state=diagram.canvas_state,
            semantic_metadata=diagram.semantic_metadata,
        )

    @property
    def is_empty(self) -> bool:
        return not self.canvas_state and not self.semantic_metadata
