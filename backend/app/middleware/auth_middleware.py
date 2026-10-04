from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.constants.roles import RoleId
from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException, error_response
from app.middleware.jwt_handler import TokenPayload, verify_token

# Routes reachable without a token. Everything else requires "Authorization: Bearer <token>".
PUBLIC_PATHS = {
    "/health",
    f"{settings.API_PREFIX}/auth/login",
    "/openapi.json",
}
PUBLIC_PREFIXES = ("/docs", "/redoc")


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)


class AuthMiddleware(BaseHTTPMiddleware):
    """Verifies the bearer token on every non-public request.

    On success the decoded claims are stored on `request.state.user`
    (a TokenPayload) for route dependencies to read.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS" or is_public(request.url.path):
            return await call_next(request)

        scheme, _, token = request.headers.get("Authorization", "").partition(" ")

        if scheme.lower() != "bearer" or not token:
            return error_response(401, "Not authenticated")

        try:
            request.state.user = verify_token(token)
        except UnauthorizedException as exc:
            return error_response(exc.status_code, exc.detail)

        return await call_next(request)


# Only used so Swagger UI shows the "Authorize" button; the middleware does the checking.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    user = getattr(request.state, "user", None)

    if user is None:
        raise UnauthorizedException()

    return user


def require_roles(*roles: RoleId):
    """Route dependency: allow only the given roles, e.g. Depends(require_roles(RoleId.ADMIN))."""
    allowed = {int(role) for role in roles}

    def checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role_id not in allowed:
            raise ForbiddenException()

        return user

    return checker
