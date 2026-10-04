from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.talk_session import TalkSession


class TalkSessionAudio(Base):
    """Audio analysis for a session (1:1 with talk_session)."""

    __tablename__ = "talk_session_audio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    talk_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("talk_session.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    filler_word_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    long_pauses_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    talk_session: Mapped["TalkSession"] = relationship(back_populates="audio")
    mispronounced_words: Mapped[list["MispronouncedWord"]] = relationship(
        back_populates="audio", cascade="all, delete-orphan", passive_deletes=True
    )
    repeated_words: Mapped[list["RepeatedWord"]] = relationship(
        back_populates="audio", cascade="all, delete-orphan", passive_deletes=True
    )


class MispronouncedWord(Base):
    """Mispronounced words flagged in a session's audio (1:many)."""

    __tablename__ = "mispronounced_words"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    talk_session_audio_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("talk_session_audio.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    audio: Mapped["TalkSessionAudio"] = relationship(
        back_populates="mispronounced_words"
    )


class RepeatedWord(Base):
    """Repeated words flagged in a session's audio (1:many)."""

    __tablename__ = "repeated_words"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    talk_session_audio_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("talk_session_audio.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    audio: Mapped["TalkSessionAudio"] = relationship(back_populates="repeated_words")
