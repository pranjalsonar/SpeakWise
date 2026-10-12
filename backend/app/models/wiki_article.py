from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.db.base import Base


class WikiArticle(Base):
    """Local cache of a parsed Wikipedia article (plain text split into sections).

    Re-checked against Wikipedia's latest revision after WIKI_CACHE_DAYS.
    """

    __tablename__ = "wiki_articles"
    __table_args__ = (UniqueConstraint("lang", "page_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lang: Mapped[str] = mapped_column(String(16), nullable=False)  # "en" | "simple"
    page_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    revision_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    # [{"heading": str|None, "path": [str], "level": int, "paragraphs": [str], "words": int, "list_ratio": float}]
    # Deferred: only loaded when building reading material, never in list queries.
    sections: Mapped[list[dict[str, Any]]] = deferred(mapped_column(JSONB, nullable=False))
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
