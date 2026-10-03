import uuid
from unittest.mock import AsyncMock

import pytest

from app.common.settings import Settings
from app.domain.entities.models.user import User
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.presentation.fastapi.routes.websocket_routes import resolve_participant

PHOTO = "https://lh3.googleusercontent.com/a/ana"


@pytest.fixture
def authenticate() -> AsyncMock:
    return AsyncMock(spec=AuthenticateUser)


async def test_should_carry_signed_in_user_photo_into_presence(authenticate: AsyncMock) -> None:
    user = User(email="ana@example.com", name="Ana", picture_url=PHOTO)
    authenticate.execute.return_value = user

    participant = await resolve_participant(
        token="id-token",
        share="",
        guest_name="",
        diagram_id=str(uuid.uuid4()),
        settings=Settings(auth_enabled=True),
        authenticate=authenticate,
        authorize=AsyncMock(spec=AuthorizeWorkspaceAccess),
        shared_lookup=AsyncMock(spec=GetDiagramByShareToken),
    )

    assert participant is not None
    assert (participant.name, participant.user_id, participant.picture_url) == (
        "Ana",
        str(user.id),
        PHOTO,
    )
