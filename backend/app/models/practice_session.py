from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.enums.practice_session import SessionMode, SessionStatus




class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    mode = Column(
        String,
        default=SessionMode.CUSTOM.value,
        nullable=False,
    )
    topic = Column(String, nullable=True)

    status = Column(
        String,
        default=SessionStatus.CREATED.value,
        nullable=False,
    )

    selected_duration = Column(Integer, nullable=True)
    topic_title = Column(
    String,
    nullable=True,
    )

    topic_category = Column(
        String,
        nullable=True,
    )

    topic_difficulty = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="practice_sessions",
    )
    