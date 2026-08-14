from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.practice_session import (
    PracticeSessionCreate,
    PracticeSessionResponse,
)
from app.services.practice_session_service import (
    create_new_session,
)

router = APIRouter(
    prefix="/sessions",
    tags=["Practice Sessions"]
)


@router.post(
    "",
    response_model=PracticeSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    session: PracticeSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_new_session(
        db=db,
        session=session,
        user_id=current_user.id,
    )