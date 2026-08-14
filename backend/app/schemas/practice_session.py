from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.enums.practice_session import (
    SessionMode,
    SessionStatus,
)


class PracticeSessionCreate(BaseModel):
    title: str
    mode: SessionMode
    topic: Optional[str] = None
    selected_duration: Optional[int] = None


class PracticeSessionUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    status: Optional[SessionStatus] = None
    selected_duration: Optional[int] = None


class PracticeSessionResponse(BaseModel):
    id: int
    title: str
    mode: SessionMode
    status: SessionStatus
    selected_duration: Optional[int]

    topic_title: str | None = None
    topic_category: str | None = None
    topic_difficulty: str | None = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True