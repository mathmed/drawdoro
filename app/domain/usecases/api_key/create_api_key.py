import uuid

from pydantic import Field

from app.domain.constants.api_keys import API_KEY_LABEL_MAX_LENGTH, API_KEY_VISIBLE_CHARS
from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.created_api_key import CreatedApiKey
from app.domain.services.api_key_secret import generate_api_key_secret, hash_api_key_secret


class CreateApiKeyParams(InputData):
    user_id: uuid.UUID
    label: str = Field(min_length=1, max_length=API_KEY_LABEL_MAX_LENGTH)


class CreateApiKey(Usecase[CreateApiKeyParams, CreatedApiKey]):
    def __init__(self, repo: ApiKeyRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateApiKeyParams) -> CreatedApiKey:
        secret = generate_api_key_secret()
        api_key = await self._repo.create(
            ApiKey(
                user_id=params.user_id,
                label=params.label.strip(),
                prefix=secret[:API_KEY_VISIBLE_CHARS],
                key_hash=hash_api_key_secret(secret),
            )
        )
        return CreatedApiKey(api_key=api_key, secret=secret)
