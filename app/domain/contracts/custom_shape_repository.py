import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.custom_shape import CustomShape


class CustomShapeRepository(ABC):
    @abstractmethod
    async def create(self, shape: CustomShape) -> CustomShape: ...

    @abstractmethod
    async def get_by_id(self, shape_id: uuid.UUID) -> CustomShape | None: ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[CustomShape]: ...

    @abstractmethod
    async def delete(self, shape_id: uuid.UUID) -> None: ...
