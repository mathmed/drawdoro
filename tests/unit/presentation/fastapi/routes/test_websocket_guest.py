import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.presentation.fastapi.routes.websocket_routes import resolve_guest


@pytest.fixture
def shared_lookup() -> AsyncMock:
    return AsyncMock(spec=GetDiagramByShareToken)


async def test_should_reject_guest_without_share_token(shared_lookup: AsyncMock) -> None:
    result = await resolve_guest("", "Ana", str(uuid.uuid4()), shared_lookup)
    assert result is None
    shared_lookup.execute.assert_not_awaited()


async def test_should_admit_guest_with_valid_share_token(shared_lookup: AsyncMock) -> None:
    diagram_id = uuid.uuid4()
    shared_lookup.execute.return_value = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="D")

    result = await resolve_guest("tok", "  Ana  ", str(diagram_id), shared_lookup)

    assert result is not None
    assert result.name == "Ana"
    assert result.user_id is None


async def test_should_fall_back_to_guest_label_when_name_blank(shared_lookup: AsyncMock) -> None:
    diagram_id = uuid.uuid4()
    shared_lookup.execute.return_value = Diagram(id=diagram_id, project_id=uuid.uuid4(), name="D")

    result = await resolve_guest("tok", "   ", str(diagram_id), shared_lookup)

    assert result is not None
    assert result.name == "Guest"


async def test_should_reject_guest_when_token_belongs_to_other_diagram(
    shared_lookup: AsyncMock,
) -> None:
    shared_lookup.execute.return_value = Diagram(id=uuid.uuid4(), project_id=uuid.uuid4(), name="D")
    result = await resolve_guest("tok", "Ana", str(uuid.uuid4()), shared_lookup)
    assert result is None


async def test_should_reject_guest_for_unknown_token(shared_lookup: AsyncMock) -> None:
    shared_lookup.execute.side_effect = NotFoundError("missing")
    result = await resolve_guest("tok", "Ana", str(uuid.uuid4()), shared_lookup)
    assert result is None
