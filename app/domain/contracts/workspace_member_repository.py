import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails


class WorkspaceMemberRepository(ABC):
    @abstractmethod
    async def get(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> WorkspaceMember | None: ...

    @abstractmethod
    async def list_details(self, workspace_id: uuid.UUID) -> list[WorkspaceMemberDetails]: ...

    @abstractmethod
    async def create(self, member: WorkspaceMember) -> WorkspaceMember: ...

    @abstractmethod
    async def update(self, member: WorkspaceMember) -> WorkspaceMember: ...

    @abstractmethod
    async def delete(self, member_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def count_owners(self, workspace_id: uuid.UUID) -> int: ...
