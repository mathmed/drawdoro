from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.entities.objects.cursor_position import CanvasPoint, CursorPosition
from app.presentation.fastapi.schemas.cursor_schemas import CursorMessageRequest


def parse(message: dict[str, Any]) -> CursorPosition | None:
    return CursorMessageRequest.model_validate(message).to_position()


def test_should_read_a_cursor_on_the_canvas() -> None:
    position = parse({"type": "cursor", "point": {"x": 10, "y": -2.5}, "page": "page:a_B-9"})

    assert position == CursorPosition(point=CanvasPoint(x=10, y=-2.5), page_id="page:a_B-9")


def test_should_read_a_pointer_that_left_the_canvas() -> None:
    assert parse({"type": "cursor", "point": None}) is None


def test_should_accept_the_largest_coordinates() -> None:
    position = parse(
        {"type": "cursor", "point": {"x": -10_000_000, "y": 10_000_000}, "page": "page:page"}
    )

    assert position == CursorPosition(
        point=CanvasPoint(x=-10_000_000, y=10_000_000), page_id="page:page"
    )


@pytest.mark.parametrize(
    "message",
    [
        {"type": "cursor"},
        {"type": "update", "point": None},
        {"type": "cursor", "point": {"x": 1, "y": 2}},
        {"type": "cursor", "point": {"x": 1, "y": 2}, "page": None},
        {"type": "cursor", "point": {"x": 1}, "page": "page:page"},
        {"type": "cursor", "point": {"x": "1", "y": 2}, "page": "page:page"},
        {"type": "cursor", "point": {"x": True, "y": 2}, "page": "page:page"},
        {"type": "cursor", "point": {"x": float("nan"), "y": 2}, "page": "page:page"},
        {"type": "cursor", "point": {"x": float("inf"), "y": 2}, "page": "page:page"},
        {"type": "cursor", "point": {"x": 10_000_001, "y": 2}, "page": "page:page"},
        {"type": "cursor", "point": {"x": 1, "y": -10_000_001}, "page": "page:page"},
        {"type": "cursor", "point": {"x": 1, "y": 2, "z": 3}, "page": "page:page"},
        {"type": "cursor", "point": [1, 2], "page": "page:page"},
        {"type": "cursor", "point": {"x": 1, "y": 2}, "page": "shape:abc"},
        {"type": "cursor", "point": {"x": 1, "y": 2}, "page": "page:" + "a" * 65},
        {"type": "cursor", "point": {"x": 1, "y": 2}, "page": "page:a b"},
        {"type": "cursor", "point": None, "page": "page:page", "id": "someone-else"},
    ],
)
def test_should_reject_a_malformed_cursor(message: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        CursorMessageRequest.model_validate(message)
