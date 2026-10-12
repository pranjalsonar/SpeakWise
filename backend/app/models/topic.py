from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.topic_category import TopicCategory


class Topic(Base):
    """A speaking topic: curated by admins, or typed by a user (custom)."""

    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 3", name="difficulty_range"),
        CheckConstraint("source IN ('curated', 'custom')", name="source_valid"),
        Index("ix_topics_source_is_active", "source", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    teaser: Mapped[str | None] = mapped_column(String(500))
    category_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("topic_categories.id", ondelete="SET NULL")
    )
    difficulty: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("2")
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    # Lowercased, punctuation/filler-free title: "Should AI tutors…?" -> "ai tutors replace homework help".
    # Unique, so the same custom topic typed twice is stored once.
    normalized_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["TopicCategory | None"] = relationship()
    wiki_sources: Mapped[list["TopicWikiSource"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TopicWikiSource.rank",
    )


class TopicWikiSource(Base):
    """Wikipedia articles that back a topic, best first (curated by hand, or found by search)."""

    __tablename__ = "topic_wiki_sources"
    __table_args__ = (UniqueConstraint("topic_id", "lang", "page_title"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    lang: Mapped[str] = mapped_column(String(16), nullable=False)  # "en" | "simple"
    page_title: Mapped[str] = mapped_column(String(255), nullable=False)

    topic: Mapped["Topic"] = relationship(back_populates="wiki_sources")
