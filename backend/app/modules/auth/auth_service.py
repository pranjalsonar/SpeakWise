from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.middleware.jwt_handler import TokenPayload, create_access_token, revoke_token
from app.modules.auth import auth_repository
from app.modules.auth.auth_helpers import DUMMY_PASSWORD_HASH, verify_password
from app.modules.auth.auth_schemas import LoginResponse, UserResponse

INVALID_CREDENTIALS = "Invalid email or password"


def login(db: Session, email: str, password: str) -> LoginResponse:
    user = auth_repository.get_user_by_email(db, email)

    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise UnauthorizedException(INVALID_CREDENTIALS)

    if not verify_password(password, user.hashed_password):
        raise UnauthorizedException(INVALID_CREDENTIALS)

    if not user.is_active:
        raise ForbiddenException("Account is disabled")

    token, expires_at = create_access_token(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role_id=user.role_id,
        role=user.role.name,
    )

    return LoginResponse(
        access_token=token,
        expires_in=int((expires_at - datetime.now(timezone.utc)).total_seconds()),
        expires_at=expires_at,
        user=UserResponse.from_model(user),
    )


def logout(current_user: TokenPayload) -> None:
    revoke_token(current_user)


def get_profile(db: Session, current_user: TokenPayload) -> UserResponse:
    user = auth_repository.get_user_by_id(db, current_user.user_id)

    # The token is still valid but the account was deleted or disabled since login.
    if user is None or not user.is_active:
        raise UnauthorizedException("User no longer has access")

    return UserResponse.from_model(user)
