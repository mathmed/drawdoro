import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails


class ListWorkspaceMembersParams(InputData):
    workspace_id: uuid.UUID


class ListWorkspaceMembers(Usecase[ListWorkspaceMembersParams, list[WorkspaceMemberDetails]]):
    def __init__(self, members: WorkspaceMemberRepository) -> None:
        self._members = members

    async def execute(self, params: ListWorkspaceMembersParams) -> list[WorkspaceMemberDetails]:
        return await self._members.list_details(params.workspace_id)
