from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class ReadingMaterial(Base):
    """One immutable version of a topic's reading material.

    Never edited after creation, so a recorded talk session always points at exactly
    what the user read. A topic gets a new version when a user has recorded all
    existing ones (up to READING_MAX_VERSIONS).
    """

    __tablename__ = "reading_materials"
    __table_args__ = (UniqueConstraint("topic_id", "version_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    lang: Mapped[str] = mapped_column(String(16), nullable=False)
    # {"summary": str, "keyPoints": [str], "sections": [{"heading": str, "paragraphs": [str]}]}
    content: Mapped[dict[str, Any]] = deferred(mapped_column(JSONB, nullable=False))
    # "<lang>:<page_id>:<section_index>" for every section piece used; later versions avoid these.
    unit_keys: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    read_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    topic: Mapped["Topic"] = relationship()
    sources: Mapped[list["ReadingMaterialSource"]] = relationship(
        back_populates="reading_material",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ReadingMaterialSource.id",
    )


class ReadingMaterialSource(Base):
    """Attribution for a reading-material version (Wikipedia is CC BY-SA 4.0).

    Title, URL and revision are snapshots, so attribution stays exact even after the
    cached article is refreshed.
    """

    __tablename__ = "reading_material_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reading_material_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("reading_materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    wiki_article_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("wiki_articles.id", ondelete="SET NULL"), index=True
    )
    lang: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    revision_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    reading_material: Mapped["ReadingMaterial"] = relationship(back_populates="sources")
