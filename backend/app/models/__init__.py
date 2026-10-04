# Import every model here so Base.metadata is complete for Alembic.
from app.models.ai_feedback import AiFeedback, AiFeedbackAlternateWord
from app.models.role import Role
from app.models.talk_session import TalkSession
from app.models.talk_session_audio import (
    MispronouncedWord,
    RepeatedWord,
    TalkSessionAudio,
)
from app.models.talk_session_summary import TalkSessionSummary
from app.models.talk_session_video import TalkSessionVideo
from app.models.user import User

__all__ = [
    "AiFeedback",
    "AiFeedbackAlternateWord",
    "MispronouncedWord",
    "RepeatedWord",
    "Role",
    "TalkSession",
    "TalkSessionAudio",
    "TalkSessionSummary",
    "TalkSessionVideo",
    "User",
]
