import uuid
from datetime import UTC, datetime

from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import NotFoundError


class RevokeApiKeyParams(InputData):
    user_id: uuid.UUID
    key_id: uuid.UUID


class RevokeApiKey(Usecase[RevokeApiKeyParams, None]):
    def __init__(self, repo: ApiKeyRepository) -> None:
        self._repo = repo

    async def execute(self, params: RevokeApiKeyParams) -> None:
        # Someone else's key is reported as missing, so key ids don't leak between users.
        api_key = await self._repo.get_active(params.key_id, params.user_id)
        if api_key is None:
            raise NotFoundError("API key not found")
        await self._repo.revoke(api_key.id, datetime.now(UTC))
