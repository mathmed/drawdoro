import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.constants.api_keys import API_KEY_LABEL_MAX_LENGTH


class CreateApiKeyRequest(BaseModel):
    label: str = Field(min_length=1, max_length=API_KEY_LABEL_MAX_LENGTH)


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None


class CreatedApiKeyResponse(ApiKeyResponse):
    # Shown once; only its hash is stored.
    secret: str
