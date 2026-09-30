from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.base_model import BaseModel


# Returned once, when the key is created: the secret cannot be read back afterwards.
class CreatedApiKey(BaseModel):
    api_key: ApiKey
    secret: str
