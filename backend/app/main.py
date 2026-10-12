import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.token_blacklist import token_blacklist
from app.modules.auth.auth_controller import router as auth_router
from app.modules.dashboard.dashboard_controller import router as dashboard_router
from app.modules.health.health_controller import router as health_router
from app.modules.reading.reading_controller import router as reading_router
from app.modules.topics.topics_controller import router as topics_router
from app.modules.users.users_controller import router as users_router

logger = logging.getLogger("speakwise")

BLACKLIST_SWEEP_SECONDS = 10 * 60


async def sweep_token_blacklist() -> None:
    """Every 10 minutes, drop blacklist entries whose tokens have expired."""
    while True:
        await asyncio.sleep(BLACKLIST_SWEEP_SECONDS)
        removed = token_blacklist.purge_expired()

        if removed:
            logger.info("Token blacklist sweep removed %d expired entries", removed)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sweeper = asyncio.create_task(sweep_token_blacklist())
    yield
    sweeper.cancel()


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_middleware(AuthMiddleware)
# Reading material is ~20 KB of JSON; gzip cuts it ~4x.
app.add_middleware(GZipMiddleware, minimum_size=1000)
# Added last so it wraps AuthMiddleware: 401 responses also get CORS headers,
# otherwise the browser reports a CORS error instead of the real status.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_exception_handler(AppException, app_exception_handler)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(topics_router, prefix=settings.API_PREFIX)
app.include_router(reading_router, prefix=settings.API_PREFIX)
