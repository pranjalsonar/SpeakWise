from sqlalchemy.orm import Session

from app.models.practice_session import PracticeSession
from app.schemas.practice_session import PracticeSessionCreate
from app.schemas.topic import TopicResponse


def create_practice_session(
    db: Session,
    session: PracticeSessionCreate,
    topic: TopicResponse,
    user_id: int,
):

    db_session = PracticeSession(
        title=session.title,
        mode=session.mode.value,
        status="CREATED",
        selected_duration=session.selected_duration,

        topic_title=topic.title,
        topic_category=topic.category,
        topic_difficulty=topic.difficulty,

        user_id=user_id,
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session


def get_practice_sessions(
    db: Session,
    user_id: int,
):

    return (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == user_id)
        .order_by(PracticeSession.created_at.desc())
        .all()
    )


def get_practice_session(
    db: Session,
    session_id: int,
    user_id: int,
):

    return (
        db.query(PracticeSession)
        .filter(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user_id,
        )
        .first()
    )

import inspect

print(inspect.signature(create_practice_session))