import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.middleware.token_blacklist import token_blacklist


@dataclass(frozen=True)
class TokenPayload:
    """Claims carried by a SpeakWise access token."""

    user_id: int
    email: str
    full_name: str | None
    role_id: int
    role: str
    jti: str
    issued_at: int
    expires_at: int


def create_access_token(
    *,
    user_id: int,
    email: str,
    full_name: str | None,
    role_id: int,
    role: str,
) -> tuple[str, datetime]:
    """Issue a signed JWT. Returns (token, expiry datetime in UTC)."""
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    claims = {
        "sub": str(user_id),
        "email": email,
        "name": full_name,
        "role_id": role_id,
        "role": role,
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "jti": uuid.uuid4().hex,
        "iat": issued_at,
        "exp": expires_at,
    }

    token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return token, expires_at


def verify_token(token: str) -> TokenPayload:
    """Validate signature, expiry, issuer and blacklist. Raises UnauthorizedException."""
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"require": ["sub", "jti", "iat", "exp", "iss"]},
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid token")

    if claims.get("type") != "access":
        raise UnauthorizedException("Invalid token")

    if token_blacklist.contains(claims["jti"]):
        raise UnauthorizedException("Token has been revoked")

    return TokenPayload(
        user_id=int(claims["sub"]),
        email=claims["email"],
        full_name=claims.get("name"),
        role_id=claims["role_id"],
        role=claims["role"],
        jti=claims["jti"],
        issued_at=claims["iat"],
        expires_at=claims["exp"],
    )


def revoke_token(payload: TokenPayload) -> None:
    """Blacklist a token until it would have expired on its own."""
    token_blacklist.add(payload.jti, payload.expires_at)
