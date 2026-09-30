import uuid

from app.domain.contracts.api_key_repository import ApiKeyRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.api_key import ApiKey


class ListApiKeysParams(InputData):
    user_id: uuid.UUID


class ListApiKeys(Usecase[ListApiKeysParams, list[ApiKey]]):
    def __init__(self, repo: ApiKeyRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListApiKeysParams) -> list[ApiKey]:
        return await self._repo.list_active_by_user(params.user_id)
