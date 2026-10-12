from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, model_validator

from app.constants.roles import RoleId
from app.models import User

FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role_id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, user: User) -> "UserProfileResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role_id=user.role_id,
            role=user.role.name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class AdminUserResponse(UserProfileResponse):
    """A user as admins see them: profile + activity."""

    session_count: int
    last_login_at: datetime | None
    last_session_at: datetime | None
    # The later of last_login_at and last_session_at; null if neither happened.
    last_active_at: datetime | None

    @classmethod
    def from_stats(
        cls, user: User, session_count: int, last_session_at: datetime | None
    ) -> "AdminUserResponse":
        times = [t for t in (user.last_login_at, last_session_at) if t is not None]
        return cls(
            **UserProfileResponse.from_model(user).model_dump(),
            session_count=session_count,
            last_login_at=user.last_login_at,
            last_session_at=last_session_at,
            last_active_at=max(times) if times else None,
        )


class UserCounts(BaseModel):
    all: int
    active: int
    inactive: int


class UserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int  # users matching search/status
    skip: int
    limit: int
    counts: UserCounts  # across all users, ignoring search/status


class CreatedUserResponse(BaseModel):
    user: AdminUserResponse
    # Shown to the admin once; only its hash is stored.
    temporary_password: str


class PasswordResetResponse(BaseModel):
    temporary_password: str


class _PartialUpdate(BaseModel):
    """PATCH body: only the fields sent are changed. Unknown fields are rejected."""

    model_config = ConfigDict(extra="forbid")

    # Fields that may be sent as null to clear them.
    NULLABLE_FIELDS: ClassVar[frozenset[str]] = frozenset({"full_name"})

    @model_validator(mode="after")
    def check_fields(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")

        for name in self.model_fields_set - self.NULLABLE_FIELDS:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")

        return self


class UpdateMyProfileRequest(_PartialUpdate):
    """What any user may change about their own account."""

    full_name: FullName | None = None
    email: EmailStr | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"full_name": "Raj Patil", "email": "raj@gmail.com"}},
    )


class AdminCreateUserRequest(BaseModel):
    """New account created by an admin. The backend generates a temporary password."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"full_name": "Nina Patel", "email": "nina@example.com", "role_id": 2}
        },
    )

    full_name: FullName
    email: EmailStr
    role_id: RoleId = RoleId.USER
    is_active: bool = True


class AdminUpdateUserRequest(UpdateMyProfileRequest):
    """What an admin may change about any account."""

    role_id: RoleId | None = None
    is_active: bool | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"full_name": "Raj Patil", "role_id": 2, "is_active": True}},
    )
