import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.config import settings
from app.services import jobs

# Auth, users and the old /analyze route (Postgres) are parked for the demo; the mobile app
# keeps the profile and history on the phone in SQLite.

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _warm_up():
    """Download MediaPipe/embedding models and load them so the first job isn't slow."""
    from app.services.analysis.context import get_embedder
    from app.services.analysis.vision import ensure_models
    try:
        ensure_models()
        get_embedder()
        logging.getLogger(__name__).info("Models ready")
    except Exception:
        logging.getLogger(__name__).exception("Model warm-up failed (will retry on first job)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    jobs.init()
    threading.Thread(target=_warm_up, daemon=True).start()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Powered Public Speaking Coach",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(jobs_router)
