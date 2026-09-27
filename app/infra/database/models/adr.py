import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.workspace import Base


class AdrORM(Base):
    __tablename__ = "adrs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    diagram_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("diagrams.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    context: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(Text)
    consequences: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
