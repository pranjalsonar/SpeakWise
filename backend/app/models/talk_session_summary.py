from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ai_feedback import AiFeedback
    from app.models.talk_session import TalkSession


class TalkSessionSummary(Base):
    """Transcript + summary for a session (1:1 with talk_session)."""

    __tablename__ = "talk_session_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    talk_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("talk_session.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    topic_name: Mapped[str | None] = mapped_column(String(255))
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    talk_session: Mapped["TalkSession"] = relationship(back_populates="summary")
    ai_feedback: Mapped["AiFeedback | None"] = relationship(
        back_populates="summary",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
