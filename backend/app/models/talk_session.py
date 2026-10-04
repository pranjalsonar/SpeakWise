from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.talk_session_audio import TalkSessionAudio
    from app.models.talk_session_summary import TalkSessionSummary
    from app.models.talk_session_video import TalkSessionVideo
    from app.models.user import User


class TalkSession(Base):
    """Core table: one recorded talk by a user."""

    __tablename__ = "talk_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    context: Mapped[str | None] = mapped_column(Text)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="talk_sessions")

    # 1:1 children (enforced by UNIQUE on each child's talk_session_id)
    audio: Mapped["TalkSessionAudio | None"] = relationship(
        back_populates="talk_session",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    video: Mapped["TalkSessionVideo | None"] = relationship(
        back_populates="talk_session",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    summary: Mapped["TalkSessionSummary | None"] = relationship(
        back_populates="talk_session",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
