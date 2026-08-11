from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token
from app.crud.user import get_user_by_email
from app.schemas.auth import LoginRequest, Token


def login_user(db: Session, login_data: LoginRequest) -> Token:

    user = get_user_by_email(db, login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(
        login_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        data={
            "sub": user.email
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )