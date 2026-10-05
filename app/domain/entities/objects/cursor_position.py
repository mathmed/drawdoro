from dataclasses import dataclass


@dataclass(frozen=True)
class CanvasPoint:
    x: float
    y: float


# Where someone's pointer is, in page coordinates, so every viewer can draw it at their own zoom.
@dataclass(frozen=True)
class CursorPosition:
    point: CanvasPoint
    page_id: str
