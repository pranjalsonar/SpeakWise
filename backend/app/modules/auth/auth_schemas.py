from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import User
from app.modules.auth.auth_helpers import MAX_PASSWORD_BYTES


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_BYTES)

    model_config = {
        "json_schema_extra": {"example": {"email": "admin@speakwise.com", "password": "admin@123"}}
    }


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role_id: int
    role: str
    is_active: bool

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role_id=user.role_id,
            role=user.role.name,
            is_active=user.is_active,
        )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    expires_at: datetime
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
