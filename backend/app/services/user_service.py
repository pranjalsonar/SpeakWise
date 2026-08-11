from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password
from app.crud.user import create_user, get_user_by_email
from app.schemas.user import UserCreate


def register_user(db: Session, user: UserCreate):

    existing_user = get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Hash the password before saving
    user.password = hash_password(user.password)

    return create_user(db, user)