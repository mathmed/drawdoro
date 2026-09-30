import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.models.api_key import ApiKey


class ApiKeyRepository(ABC):
    @abstractmethod
    async def create(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    async def list_active_by_user(self, user_id: uuid.UUID) -> list[ApiKey]: ...

    @abstractmethod
    async def get_active_by_hash(self, key_hash: str) -> ApiKey | None: ...

    @abstractmethod
    async def get_active(self, key_id: uuid.UUID, user_id: uuid.UUID) -> ApiKey | None: ...

    @abstractmethod
    async def revoke(self, key_id: uuid.UUID, revoked_at: datetime) -> None: ...

    @abstractmethod
    async def mark_used(self, key_id: uuid.UUID, used_at: datetime) -> None: ...
