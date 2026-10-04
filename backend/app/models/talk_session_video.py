from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.talk_session import TalkSession


class TalkSessionVideo(Base):
    """Video analysis for a session (1:1 with talk_session)."""

    __tablename__ = "talk_session_video"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    talk_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("talk_session.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    posture_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    head_movement_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    hand_gesture_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    talk_session: Mapped["TalkSession"] = relationship(back_populates="video")
