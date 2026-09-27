import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.adr import Adr


class AdrRepository(ABC):
    @abstractmethod
    async def create(self, adr: Adr) -> Adr: ...

    @abstractmethod
    async def get_by_id(self, adr_id: uuid.UUID) -> Adr | None: ...

    @abstractmethod
    async def list_by_diagram(self, diagram_id: uuid.UUID) -> list[Adr]: ...

    @abstractmethod
    async def update(self, adr: Adr) -> Adr: ...

    @abstractmethod
    async def delete(self, adr_id: uuid.UUID) -> None: ...
