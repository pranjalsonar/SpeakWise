from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.speech import router as speech_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Powered Public Speaking Coach"
)

app.include_router(health_router)
app.include_router(speech_router)