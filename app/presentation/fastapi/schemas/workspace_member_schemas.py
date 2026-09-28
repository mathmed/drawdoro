import uuid

from pydantic import BaseModel, ConfigDict

from app.domain.enums.workspace_role import WorkspaceRole


class AddWorkspaceMemberRequest(BaseModel):
    email: str
    role: WorkspaceRole = WorkspaceRole.EDITOR


class UpdateWorkspaceMemberRoleRequest(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    email: str
    role: WorkspaceRole
