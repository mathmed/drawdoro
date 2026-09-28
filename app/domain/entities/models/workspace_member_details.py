import uuid

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.workspace_role import WorkspaceRole


class WorkspaceMemberDetails(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    role: WorkspaceRole
