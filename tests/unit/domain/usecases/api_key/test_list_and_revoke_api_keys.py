import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.entities.models.api_key import ApiKey
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.api_key.list_api_keys import ListApiKeys, ListApiKeysParams
from app.domain.usecases.api_key.revoke_api_key import RevokeApiKey, RevokeApiKeyParams

USER_ID = uuid.uuid4()
KEY = ApiKey(user_id=USER_ID, label="laptop", prefix="mcpk_abc", key_hash="hash")


@pytest.fixture
def repo() -> ApiKeyRepository:
    return cast(ApiKeyRepository, create_autospec(ApiKeyRepository))


@pytest.fixture
def sut(repo: ApiKeyRepository) -> RevokeApiKey:
    return RevokeApiKey(repo)


async def test_should_list_the_users_active_keys(repo: ApiKeyRepository) -> None:
    repo.list_active_by_user = AsyncMock(return_value=[KEY])  # type: ignore[method-assign]
    assert await ListApiKeys(repo).execute(ListApiKeysParams(user_id=USER_ID)) == [KEY]
    repo.list_active_by_user.assert_awaited_once_with(USER_ID)


async def test_should_revoke_own_key(sut: RevokeApiKey, repo: ApiKeyRepository) -> None:
    repo.get_active = AsyncMock(return_value=KEY)  # type: ignore[method-assign]
    await sut.execute(RevokeApiKeyParams(user_id=USER_ID, key_id=KEY.id))
    repo.get_active.assert_awaited_once_with(KEY.id, USER_ID)
    call = cast(AsyncMock, repo.revoke).await_args
    assert call is not None
    key_id, revoked_at = call.args
    assert key_id == KEY.id
    assert revoked_at.tzinfo is not None


async def test_should_report_someone_elses_key_as_missing(
    sut: RevokeApiKey, repo: ApiKeyRepository
) -> None:
    repo.get_active = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        await sut.execute(RevokeApiKeyParams(user_id=uuid.uuid4(), key_id=KEY.id))
    cast(AsyncMock, repo.revoke).assert_not_awaited()
