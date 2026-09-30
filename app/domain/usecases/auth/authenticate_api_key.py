from datetime import UTC, datetime, timedelta

from app.domain.constants.api_keys import API_KEY_LAST_USED_RESOLUTION_SECONDS
from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.api_key_owner import ApiKeyOwner
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.services.api_key_secret import hash_api_key_secret


class AuthenticateApiKeyParams(InputData):
    secret: str


class AuthenticateApiKey(Usecase[AuthenticateApiKeyParams, ApiKeyOwner]):
    def __init__(self, keys: ApiKeyRepository, users: UserRepository) -> None:
        self._keys = keys
        self._users = users

    async def execute(self, params: AuthenticateApiKeyParams) -> ApiKeyOwner:
        api_key = await self._keys.get_active_by_hash(hash_api_key_secret(params.secret))
        if api_key is None:
            raise UnauthorizedError("Invalid or revoked API key")
        user = await self._users.get_by_id(api_key.user_id)
        if user is None:
            raise UnauthorizedError("Invalid or revoked API key")
        now = datetime.now(UTC)
        stale_after = timedelta(seconds=API_KEY_LAST_USED_RESOLUTION_SECONDS)
        if api_key.last_used_at is None or now - api_key.last_used_at >= stale_after:
            await self._keys.mark_used(api_key.id, now)
            api_key.last_used_at = now
        return ApiKeyOwner(api_key=api_key, user=user)
