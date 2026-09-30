from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.base_model import BaseModel
from app.domain.entities.models.user import User


class ApiKeyOwner(BaseModel):
    api_key: ApiKey
    user: User
