from typing import cast
from unittest.mock import AsyncMock

import pytest

from app.common.settings import Settings
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.api_key_owner import ApiKeyOwner
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.presentation.fastapi.dependencies.current_user import (
    Caller,
    get_caller,
    get_session_user,
)

ANA = User(email="ana@example.com", name="Ana")
ANAS_KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_abc", key_hash="hash")
AUTH_ON = Settings(auth_enabled=True, service_api_key="svc-key")


@pytest.fixture
def authenticate() -> AuthenticateUser:
    mock = AsyncMock(spec=AuthenticateUser)
    mock.execute.return_value = ANA
    return cast(AuthenticateUser, mock)


@pytest.fixture
def authenticate_key() -> AuthenticateApiKey:
    mock = AsyncMock(spec=AuthenticateApiKey)
    mock.execute.return_value = ApiKeyOwner(api_key=ANAS_KEY, user=ANA)
    return cast(AuthenticateApiKey, mock)


async def resolve(
    authenticate: AuthenticateUser,
    authenticate_key: AuthenticateApiKey,
    api_key: str | None,
    settings: Settings = AUTH_ON,
) -> Caller:
    return await get_caller(
        credentials=None,
        x_api_key=api_key,
        settings=settings,
        authenticate=authenticate,
        authenticate_key=authenticate_key,
    )


async def test_should_resolve_nobody_when_auth_is_disabled(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey
) -> None:
    caller = await resolve(authenticate, authenticate_key, "mcpk_x", Settings(auth_enabled=False))
    assert caller == Caller()


async def test_should_keep_the_shared_service_key_as_an_ownerless_caller(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey
) -> None:
    assert await resolve(authenticate, authenticate_key, "svc-key") == Caller(is_service=True)


async def test_should_resolve_a_personal_key_to_its_owner(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey
) -> None:
    caller = await resolve(authenticate, authenticate_key, "mcpk_secret")
    assert caller == Caller(user=ANA, api_key=ANAS_KEY)
    cast(AsyncMock, authenticate_key.execute).assert_awaited_once_with(
        AuthenticateApiKeyParams(secret="mcpk_secret")
    )


@pytest.mark.parametrize("api_key", [None, "wrong-key"])
async def test_should_fall_back_to_the_session_token(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey, api_key: str | None
) -> None:
    assert await resolve(authenticate, authenticate_key, api_key) == Caller(user=ANA)
    cast(AsyncMock, authenticate_key.execute).assert_not_awaited()


async def test_should_manage_keys_only_from_a_session() -> None:
    assert await get_session_user(Caller(user=ANA)) == ANA
    with pytest.raises(ForbiddenError):
        await get_session_user(Caller(user=ANA, api_key=ANAS_KEY))
    with pytest.raises(NotFoundError):
        await get_session_user(Caller())
