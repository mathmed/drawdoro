from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.workspace_role import WorkspaceRole


class WorkspaceMember(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: WorkspaceRole = WorkspaceRole.VIEWER
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
