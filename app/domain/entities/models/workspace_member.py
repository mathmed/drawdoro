import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.workspace_role import WorkspaceRole


class WorkspaceMember(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole = WorkspaceRole.VIEWER
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
