import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateCommentRequest(BaseModel):
    element_id: str
    content: str
    author_id: uuid.UUID | None = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diagram_id: uuid.UUID
    element_id: str
    content: str
    author_id: uuid.UUID | None
    created_at: datetime
