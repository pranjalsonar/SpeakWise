from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants.session import (
    ALLOWED_DURATIONS,
    DEFAULT_SESSION_TITLE,
)
from app.crud.practice_session import create_practice_session
from app.enums.practice_session import SessionMode
from app.schemas.practice_session import PracticeSessionCreate
from app.services.topic_service import TopicService


def create_new_session(
    db: Session,
    session: PracticeSessionCreate,
    user_id: int,
):
    # Validate duration
    if (
        session.selected_duration is not None
        and session.selected_duration not in ALLOWED_DURATIONS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid speaking duration.",
        )

    # CUSTOM mode requires topic
    if (
        session.mode == SessionMode.CUSTOM
        and (
            session.topic is None
            or session.topic.strip() == ""
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic is required for custom mode.",
        )

    # RANDOM mode ignores user topic
    if session.mode == SessionMode.RANDOM:
        session.topic = None

    # DAILY mode ignores user topic
    if session.mode == SessionMode.DAILY:
        session.topic = None

    # Default title
    if session.title.strip() == "":
        session.title = DEFAULT_SESSION_TITLE

    # Generate topic
    topic = TopicService.get_topic(
        mode=session.mode,
        custom_topic=session.topic,
    )

    # # Create session
    # return create_practice_session(
    #     db=db,
    #     session=session,
    #     topic=topic,
    #     user_id=user_id,
    # )
    import inspect

    print("Function:", create_practice_session)
    print("Module:", create_practice_session.__module__)
    print("Signature:", inspect.signature(create_practice_session))

    return create_practice_session(
        db=db,
        session=session,
        topic=topic,
        user_id=user_id,
    )