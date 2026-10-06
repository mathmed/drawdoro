from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.entities.objects.cursor_position import CanvasPoint, CursorPosition

# Far beyond any real drawing, and small enough that every peer can still do math with it.
MAX_COORDINATE = 10_000_000
PAGE_ID_PATTERN = r"^page:[A-Za-z0-9_-]{1,64}$"


class CursorPointRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    x: float = Field(ge=-MAX_COORDINATE, le=MAX_COORDINATE, allow_inf_nan=False)
    y: float = Field(ge=-MAX_COORDINATE, le=MAX_COORDINATE, allow_inf_nan=False)


# A null point means the pointer left the canvas.
class CursorMessageRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    type: Literal["cursor"]
    point: CursorPointRequest | None
    page: str | None = Field(default=None, pattern=PAGE_ID_PATTERN)

    @model_validator(mode="after")
    def require_page_with_point(self) -> Self:
        if self.point is not None and self.page is None:
            raise ValueError("A cursor on the canvas needs its page")
        return self

    def to_position(self) -> CursorPosition | None:
        if self.point is None or self.page is None:
            return None
        return CursorPosition(point=CanvasPoint(x=self.point.x, y=self.point.y), page_id=self.page)
