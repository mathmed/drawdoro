import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest
from pydantic import ValidationError

from app.domain.constants.api_keys import API_KEY_PREFIX, API_KEY_VISIBLE_CHARS
from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.services.api_key_secret import hash_api_key_secret
from app.domain.usecases.api_key.create_api_key import CreateApiKey, CreateApiKeyParams


@pytest.fixture
def repo() -> ApiKeyRepository:
    mock = cast(ApiKeyRepository, create_autospec(ApiKeyRepository))
    mock.create = AsyncMock(side_effect=lambda created: created)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def sut(repo: ApiKeyRepository) -> CreateApiKey:
    return CreateApiKey(repo)


async def test_should_store_only_the_hash_and_return_the_secret_once(sut: CreateApiKey) -> None:
    user_id = uuid.uuid4()
    created = await sut.execute(CreateApiKeyParams(user_id=user_id, label="  laptop  "))
    assert created.secret.startswith(API_KEY_PREFIX)
    assert created.api_key.key_hash == hash_api_key_secret(created.secret)
    assert created.api_key.prefix == created.secret[:API_KEY_VISIBLE_CHARS]
    assert (created.api_key.user_id, created.api_key.label) == (user_id, "laptop")
    assert created.secret not in created.api_key.model_dump_json()


def test_should_reject_an_empty_label() -> None:
    with pytest.raises(ValidationError):
        CreateApiKeyParams(user_id=uuid.uuid4(), label="")
