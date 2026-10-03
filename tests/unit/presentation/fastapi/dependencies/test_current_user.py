from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.common.settings import Settings
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.api_key_owner import ApiKeyOwner
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)
from app.domain.usecases.auth.authenticate_user import AuthenticateUser, AuthenticateUserParams
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
    credentials: HTTPAuthorizationCredentials | None = None,
) -> Caller:
    return await get_caller(
        credentials=credentials,
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


async def test_should_authenticate_the_bearer_token(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey
) -> None:
    bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials="id-token")
    caller = await resolve(authenticate, authenticate_key, None, credentials=bearer)
    assert caller == Caller(user=ANA)
    cast(AsyncMock, authenticate.execute).assert_awaited_once_with(
        AuthenticateUserParams(token="id-token")
    )


# Without a bearer token the session check still runs, with an empty token, and rejects it.
async def test_should_check_an_empty_token_without_credentials(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey
) -> None:
    await resolve(authenticate, authenticate_key, None)
    cast(AsyncMock, authenticate.execute).assert_awaited_once_with(AuthenticateUserParams(token=""))


# An unset service key must never match, not even an empty X-API-Key header.
async def test_should_not_take_an_empty_key_for_an_unset_service_key(
    authenticate: AuthenticateUser, authenticate_key: AuthenticateApiKey
) -> None:
    settings = Settings(auth_enabled=True, service_api_key="")
    assert await resolve(authenticate, authenticate_key, "", settings) == Caller(user=ANA)


async def test_should_manage_keys_only_from_a_session() -> None:
    assert await get_session_user(Caller(user=ANA)) == ANA
    with pytest.raises(ForbiddenError) as forbidden:
        await get_session_user(Caller(user=ANA, api_key=ANAS_KEY))
    assert forbidden.value.message == "API keys can only be managed from a signed-in session"
    with pytest.raises(NotFoundError) as missing:
        await get_session_user(Caller())
    assert missing.value.message == "No signed-in user (authentication is disabled)"
