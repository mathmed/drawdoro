from datetime import UTC, datetime, timedelta, tzinfo
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.constants.api_keys import API_KEY_LAST_USED_RESOLUTION_SECONDS
from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.services.api_key_secret import hash_api_key_secret
from app.domain.usecases.auth import authenticate_api_key
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)
from tests.doubles import double

SECRET = "mcpk_secret"
INVALID_KEY = "Invalid or revoked API key"
NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
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
def keys() -> NonCallableMagicMock:
    return double(ApiKeyRepository)


@pytest.fixture
def users() -> NonCallableMagicMock:
    mock = double(UserRepository)
    mock.get_by_id.return_value = ANA
    return mock


@pytest.fixture
def sut(keys: NonCallableMagicMock, users: NonCallableMagicMock) -> AuthenticateApiKey:
    return AuthenticateApiKey(keys, users)


async def test_should_resolve_the_owner_and_mark_the_key_used(
    sut: AuthenticateApiKey, keys: NonCallableMagicMock, users: NonCallableMagicMock
) -> None:
    api_key = key()
    keys.get_active_by_hash.return_value = api_key
    owner = await sut.execute(AuthenticateApiKeyParams(secret=SECRET))
    assert owner.user == ANA
    assert owner.api_key.last_used_at is not None
    keys.get_active_by_hash.assert_awaited_once_with(hash_api_key_secret(SECRET))
    keys.mark_used.assert_awaited_once()
    users.get_by_id.assert_awaited_once_with(ANA.id)


async def test_should_not_write_last_use_on_every_call(
    sut: AuthenticateApiKey, keys: NonCallableMagicMock
) -> None:
    recent = datetime.now(UTC) - timedelta(seconds=5)
    keys.get_active_by_hash.return_value = key(last_used_at=recent)
    await sut.execute(AuthenticateApiKeyParams(secret=SECRET))
    keys.mark_used.assert_not_awaited()


async def test_should_reject_unknown_or_revoked_keys(
    sut: AuthenticateApiKey, keys: NonCallableMagicMock
) -> None:
    keys.get_active_by_hash.return_value = None
    with pytest.raises(UnauthorizedError, match=f"^{INVALID_KEY}$"):
        await sut.execute(AuthenticateApiKeyParams(secret=SECRET))


async def test_should_reject_keys_whose_owner_is_gone(
    sut: AuthenticateApiKey, keys: NonCallableMagicMock, users: NonCallableMagicMock
) -> None:
    keys.get_active_by_hash.return_value = key()
    users.get_by_id.return_value = None
    with pytest.raises(UnauthorizedError, match=f"^{INVALID_KEY}$"):
        await sut.execute(AuthenticateApiKeyParams(secret=SECRET))


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> FrozenDatetime:
        return cls.fromtimestamp(NOW.timestamp(), tz)


async def test_should_mark_the_key_used_once_its_last_use_is_exactly_stale(
    sut: AuthenticateApiKey, keys: NonCallableMagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(authenticate_api_key, "datetime", FrozenDatetime)
    stale = NOW - timedelta(seconds=API_KEY_LAST_USED_RESOLUTION_SECONDS)
    api_key = key(last_used_at=stale)
    keys.get_active_by_hash.return_value = api_key
    owner = await sut.execute(AuthenticateApiKeyParams(secret=SECRET))
    keys.mark_used.assert_awaited_once_with(api_key.id, NOW)
    assert owner.api_key.last_used_at == NOW
