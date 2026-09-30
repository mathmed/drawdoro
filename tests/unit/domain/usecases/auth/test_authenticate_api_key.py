from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.services.api_key_secret import hash_api_key_secret
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)

SECRET = "mcpk_secret"
ANA = User(email="ana@example.com", name="Ana")


def key(last_used_at: datetime | None = None) -> ApiKey:
    return ApiKey(
        user_id=ANA.id,
        label="laptop",
        prefix="mcpk_sec",
        key_hash=hash_api_key_secret(SECRET),
        last_used_at=last_used_at,
    )


@pytest.fixture
def keys() -> ApiKeyRepository:
    return cast(ApiKeyRepository, create_autospec(ApiKeyRepository))


@pytest.fixture
def users() -> UserRepository:
    mock = cast(UserRepository, create_autospec(UserRepository))
    mock.get_by_id = AsyncMock(return_value=ANA)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def sut(keys: ApiKeyRepository, users: UserRepository) -> AuthenticateApiKey:
    return AuthenticateApiKey(keys, users)


async def test_should_resolve_the_owner_and_mark_the_key_used(
    sut: AuthenticateApiKey, keys: ApiKeyRepository
) -> None:
    api_key = key()
    keys.get_active_by_hash = AsyncMock(return_value=api_key)  # type: ignore[method-assign]
    owner = await sut.execute(AuthenticateApiKeyParams(secret=SECRET))
    assert owner.user == ANA
    assert owner.api_key.last_used_at is not None
    keys.get_active_by_hash.assert_awaited_once_with(hash_api_key_secret(SECRET))
    cast(AsyncMock, keys.mark_used).assert_awaited_once()


async def test_should_not_write_last_use_on_every_call(
    sut: AuthenticateApiKey, keys: ApiKeyRepository
) -> None:
    recent = datetime.now(UTC) - timedelta(seconds=5)
    keys.get_active_by_hash = AsyncMock(return_value=key(last_used_at=recent))  # type: ignore[method-assign]
    await sut.execute(AuthenticateApiKeyParams(secret=SECRET))
    cast(AsyncMock, keys.mark_used).assert_not_awaited()


async def test_should_reject_unknown_or_revoked_keys(
    sut: AuthenticateApiKey, keys: ApiKeyRepository
) -> None:
    keys.get_active_by_hash = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(UnauthorizedError):
        await sut.execute(AuthenticateApiKeyParams(secret=SECRET))


async def test_should_reject_keys_whose_owner_is_gone(
    sut: AuthenticateApiKey, keys: ApiKeyRepository, users: UserRepository
) -> None:
    keys.get_active_by_hash = AsyncMock(return_value=key())  # type: ignore[method-assign]
    users.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(UnauthorizedError):
        await sut.execute(AuthenticateApiKeyParams(secret=SECRET))
