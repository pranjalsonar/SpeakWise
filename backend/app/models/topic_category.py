from datetime import datetime

from sqlalchemy import DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TopicCategory(Base):
    """Lookup table of topic categories. IDs are fixed and seeded by migration b47879011cfd."""

    __tablename__ = "topic_categories"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
