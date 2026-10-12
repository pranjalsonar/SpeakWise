from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base for errors raised by services. Converted to a JSON response in main.py.

    `extra` adds fields next to "detail" in the response (e.g. suggestions).
    """

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad request"

    def __init__(self, detail: str | None = None, extra: dict | None = None):
        self.detail = detail or self.detail
        self.extra = extra or {}
        super().__init__(self.detail)


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Not authenticated"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have permission to perform this action"


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists"


class UnprocessableException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "The request could not be processed"


class TooManyRequestsException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Too many requests. Please try again later"


class ServiceUnavailableException(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "A required service is temporarily unavailable. Please try again shortly"


def error_response(status_code: int, detail: str, extra: dict | None = None) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return JSONResponse(
        status_code=status_code, content={"detail": detail, **(extra or {})}, headers=headers
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return error_response(exc.status_code, exc.detail, exc.extra)
