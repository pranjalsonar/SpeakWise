from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants.roles import RoleId
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.middleware.jwt_handler import TokenPayload
from app.models import User
from app.modules.auth.auth_helpers import generate_temporary_password, hash_password
from app.modules.users import users_repository
from app.modules.users.users_repository import StatusFilter
from app.modules.users.users_schemas import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserResponse,
    CreatedUserResponse,
    PasswordResetResponse,
    UpdateMyProfileRequest,
    UserCounts,
    UserListResponse,
    UserProfileResponse,
)

EMAIL_TAKEN = "An account with this email already exists"


# ---- Own profile (any logged-in user) ----

def get_my_profile(db: Session, current_user: TokenPayload) -> UserProfileResponse:
    return UserProfileResponse.from_model(_get_active_self(db, current_user))


def update_my_profile(
    db: Session, current_user: TokenPayload, body: UpdateMyProfileRequest
) -> UserProfileResponse:
    user = _get_active_self(db, current_user)
    return UserProfileResponse.from_model(_apply_changes(db, user, body.model_dump(exclude_unset=True)))


# ---- Any user (admin only; role enforced in the controller) ----

def list_users(
    db: Session, *, search: str | None, status: StatusFilter | None, skip: int, limit: int
) -> UserListResponse:
    rows, total = users_repository.list_users_with_stats(
        db, search=search, status=status, skip=skip, limit=limit
    )
    all_users, active = users_repository.count_users_by_status(db)

    return UserListResponse(
        items=[AdminUserResponse.from_stats(user, count, last) for user, count, last in rows],
        total=total,
        skip=skip,
        limit=limit,
        counts=UserCounts(all=all_users, active=active, inactive=all_users - active),
    )


def get_user(db: Session, user_id: int) -> AdminUserResponse:
    return _with_stats(db, _get_or_404(db, user_id))


def create_user(db: Session, body: AdminCreateUserRequest) -> CreatedUserResponse:
    email = body.email.strip().lower()

    if users_repository.get_user_by_email(db, email) is not None:
        raise ConflictException(EMAIL_TAKEN)

    temporary_password = generate_temporary_password()
    user = User(
        email=email,
        full_name=body.full_name,
        role_id=body.role_id,
        is_active=body.is_active,
        hashed_password=hash_password(temporary_password),
    )

    try:
        user = users_repository.add_user(db, user)
    except IntegrityError:
        db.rollback()
        raise ConflictException(EMAIL_TAKEN)

    return CreatedUserResponse(user=_with_stats(db, user), temporary_password=temporary_password)


def update_user(
    db: Session, current_user: TokenPayload, user_id: int, body: AdminUpdateUserRequest
) -> AdminUserResponse:
    user = _get_or_404(db, user_id)
    changes = body.model_dump(exclude_unset=True)

    # Stop an admin from locking themselves out of the admin area.
    if user.id == current_user.user_id:
        if changes.get("role_id", user.role_id) != RoleId.ADMIN or changes.get("is_active") is False:
            raise ForbiddenException("You can't remove your own admin access or deactivate yourself")

    return _with_stats(db, _apply_changes(db, user, changes))


def reset_password(db: Session, user_id: int) -> PasswordResetResponse:
    """Replace a user's password with a new temporary one. Their old password stops working."""
    user = _get_or_404(db, user_id)
    temporary_password = generate_temporary_password()
    user.hashed_password = hash_password(temporary_password)
    users_repository.save_user(db, user)
    return PasswordResetResponse(temporary_password=temporary_password)


# ---- Helpers ----

def _get_active_self(db: Session, current_user: TokenPayload) -> User:
    user = users_repository.get_user_by_id(db, current_user.user_id)

    # The token is still valid but the account was deleted or disabled since login.
    if user is None or not user.is_active:
        raise UnauthorizedException("User no longer has access")

    return user


def _get_or_404(db: Session, user_id: int) -> User:
    user = users_repository.get_user_by_id(db, user_id)

    if user is None:
        raise NotFoundException("User not found")

    return user


def _with_stats(db: Session, user: User) -> AdminUserResponse:
    count, last_session_at = users_repository.get_session_stats(db, user.id)
    return AdminUserResponse.from_stats(user, count, last_session_at)


def _apply_changes(db: Session, user: User, changes: dict[str, Any]) -> User:
    if "email" in changes:
        changes["email"] = changes["email"].strip().lower()
        other = users_repository.get_user_by_email(db, changes["email"])

        if other is not None and other.id != user.id:
            raise ConflictException(EMAIL_TAKEN)

    for field, value in changes.items():
        setattr(user, field, value)

    try:
        return users_repository.save_user(db, user)
    except IntegrityError:
        # Another request took the email between the check above and the commit.
        db.rollback()
        raise ConflictException(EMAIL_TAKEN)
