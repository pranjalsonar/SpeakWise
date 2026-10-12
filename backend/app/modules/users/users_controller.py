from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.constants.roles import RoleId
from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user, require_roles
from app.middleware.jwt_handler import TokenPayload
from app.modules.users import users_service
from app.modules.users.users_repository import StatusFilter
from app.modules.users.users_schemas import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserResponse,
    CreatedUserResponse,
    PasswordResetResponse,
    UpdateMyProfileRequest,
    UserListResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])

require_admin = require_roles(RoleId.ADMIN)


# ---- Own profile ----

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The logged-in user's profile."""
    return users_service.get_my_profile(db, current_user)


@router.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    body: UpdateMyProfileRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update your own full name and/or email. Only the fields sent are changed."""
    return users_service.update_my_profile(db, current_user, body)


# ---- Admin: any user ----

@router.get("", response_model=UserListResponse)
def list_users(
    search: str | None = Query(None, max_length=255, description="Matches name or email"),
    status: StatusFilter | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _admin: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Users with session stats, newest first, plus overall counts (admin only)."""
    return users_service.list_users(db, search=search, status=status, skip=skip, limit=limit)


@router.post("", response_model=CreatedUserResponse, status_code=http_status.HTTP_201_CREATED)
def create_user(
    body: AdminCreateUserRequest,
    _admin: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create an account. Returns a temporary password to share with the user (admin only)."""
    return users_service.create_user(db, body)


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_password(
    user_id: int,
    _admin: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Give a user a new temporary password; the old one stops working (admin only)."""
    return users_service.reset_password(db, user_id)


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    _admin: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Any user's profile (admin only)."""
    return users_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    body: AdminUpdateUserRequest,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update any user's name, email, role or active status (admin only)."""
    return users_service.update_user(db, current_user, user_id, body)
