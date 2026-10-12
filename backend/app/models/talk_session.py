from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.topic_category import TopicCategory
    from app.models.talk_session_audio import TalkSessionAudio
    from app.models.talk_session_summary import TalkSessionSummary
    from app.models.talk_session_video import TalkSessionVideo
    from app.models.user import User


class TalkSession(Base):
    """Core table: one recorded talk by a user."""

    __tablename__ = "talk_session"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="duration_seconds_non_negative"),
        # "Has this user recorded this topic / this reading material?" lookups.
        Index("ix_talk_session_user_id_topic_id", "user_id", "topic_id"),
        Index("ix_talk_session_user_id_reading_material_id", "user_id", "reading_material_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    context: Mapped[str | None] = mapped_column(Text)
    topic_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("topics.id", ondelete="SET NULL")
    )
    # The exact reading-material version the user read before recording. A version the
    # user has recorded with is never served to them again (see reading_service).
    reading_material_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("reading_materials.id", ondelete="SET NULL")
    )
    # Topic chosen before recording (the AI summary may later infer its own topic_name).
    topic_title: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("topic_categories.id", ondelete="SET NULL"),
        index=True,
    )
    # Length of the recording actually spoken.
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="talk_sessions")
    category: Mapped["TopicCategory | None"] = relationship()

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
