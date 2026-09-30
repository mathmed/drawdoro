from app.domain.entities.models.base_model import BaseModel


class Identity(BaseModel):
    subject: str
    email: str
    name: str
    picture_url: str | None = None
