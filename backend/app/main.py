from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.middleware.auth_middleware import AuthMiddleware
from app.modules.auth.auth_controller import router as auth_router
from app.modules.health.health_controller import router as health_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(AuthMiddleware)
app.add_exception_handler(AppException, app_exception_handler)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_PREFIX)
