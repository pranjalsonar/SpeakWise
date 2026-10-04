from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.talk_session_summary import TalkSessionSummary


class AiFeedback(Base):
    """AI feedback generated from a summary (1:1 with talk_session_summary)."""

    __tablename__ = "ai_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    summary_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("talk_session_summary.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    summary: Mapped["TalkSessionSummary"] = relationship(back_populates="ai_feedback")
    alternate_words: Mapped[list["AiFeedbackAlternateWord"]] = relationship(
        back_populates="ai_feedback", cascade="all, delete-orphan", passive_deletes=True
    )


class AiFeedbackAlternateWord(Base):
    """A filler word and its suggested alternate (1:many with ai_feedback)."""

    __tablename__ = "ai_feedback_alternate_words"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ai_feedback_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ai_feedback.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filler_word: Mapped[str] = mapped_column(String(255), nullable=False)
    alternate_word: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ai_feedback: Mapped["AiFeedback"] = relationship(back_populates="alternate_words")
