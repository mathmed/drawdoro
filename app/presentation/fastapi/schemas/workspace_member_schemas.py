import uuid

from pydantic import BaseModel, ConfigDict

from app.domain.enums.workspace_role import WorkspaceRole
from app.presentation.fastapi.schemas.text_schemas import NulFreeStr


class AddWorkspaceMemberRequest(BaseModel):
    email: NulFreeStr
    role: WorkspaceRole = WorkspaceRole.EDITOR


class UpdateWorkspaceMemberRoleRequest(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    email: str
    role: WorkspaceRole
