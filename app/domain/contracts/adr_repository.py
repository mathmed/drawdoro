from abc import ABC, abstractmethod

from app.domain.entities.models.adr import Adr


class AdrRepository(ABC):
    @abstractmethod
    def create(self, _adr: Adr) -> Adr: ...

    @abstractmethod
    def get_by_id(self, _adr_id: str) -> Adr | None: ...

    @abstractmethod
    def list_by_diagram(self, _diagram_id: str) -> list[Adr]: ...

    @abstractmethod
    def update(self, _adr: Adr) -> Adr: ...

    @abstractmethod
    def delete(self, _adr_id: str) -> None: ...
