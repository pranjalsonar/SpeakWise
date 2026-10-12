from fastapi import APIRouter, Depends, Query, Response
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.jwt_handler import TokenPayload
from app.modules.topics import topics_service
from app.modules.topics.topics_schemas import (
    CustomTopicRequest,
    CustomTopicResponse,
    DailyTopicResponse,
    SuggestTopicResponse,
    TopicResponse,
)

router = APIRouter(prefix="/topics", tags=["Topics"])


@router.get("/suggest", response_model=SuggestTopicResponse)
def suggest_topic(
    category: str | None = Query(None, description="Category name, e.g. Technology"),
    difficulty: str | None = Query(None, description="Beginner | Intermediate | Advanced"),
    exclude_id: int | None = Query(None, description="Current topic, so a reroll gives a different one"),
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A random curated topic the user hasn't recorded a talk on yet."""
    return topics_service.suggest_topic(db, current_user, category, difficulty, exclude_id)


@router.get("/daily", response_model=DailyTopicResponse)
def daily_topic(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Today's topic (same for everyone), with whether this user already recorded it."""
    return topics_service.daily_topic(db, current_user)


@router.post("/custom", response_model=CustomTopicResponse)
def create_custom_topic(
    body: CustomTopicRequest,
    response: Response,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Turn user-typed text into a topic backed by Wikipedia articles.

    201 when a new topic is created, 200 when an identical one already existed,
    422 (with `suggestion` and `related_topics`) when Wikipedia has nothing relevant.
    """
    result = topics_service.create_custom_topic(db, current_user, body.text)
    response.status_code = http_status.HTTP_201_CREATED if result.created else http_status.HTTP_200_OK
    return result


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: int,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return topics_service.get_topic(db, current_user, topic_id)
