from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import register_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return register_user(db, user)
@router.get(
    "/me",
    response_model=UserResponse
)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user