from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.jwt_handler import TokenPayload
from app.modules.auth import auth_service
from app.modules.auth.auth_schemas import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Exchange email + password for a bearer access token."""
    return auth_service.login(db, body.email, body.password)


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: TokenPayload = Depends(get_current_user)):
    """Revoke the current token (blacklisted until it expires)."""
    auth_service.logout(current_user)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def me(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the logged-in user's profile."""
    return auth_service.get_profile(db, current_user)
