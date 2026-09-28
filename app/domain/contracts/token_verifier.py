from abc import ABC, abstractmethod

from app.domain.entities.models.identity import Identity


class TokenVerifier(ABC):
    @abstractmethod
    async def verify(self, token: str) -> Identity: ...
