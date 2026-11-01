from fastapi import APIRouter

from app.core.config import settings
from app.services.content import _articles

router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "Welcome to SpeakWise API!"
    }


@router.get("/about")
def about():
    return {
        "project": "SpeakWise",
        "version": "1.0",
        "description": "AI Powered Public Speaking Coach"
    }


@router.get("/health")
def health():
    """Used by the app before uploading. Never exposes the keys themselves."""
    return {
        "status": "ok",
        "version": settings.VERSION,
        "articles": len(_articles()),
        "access_key_required": bool(settings.APP_TOKEN),
        "providers": {
            "groq": bool(settings.GROQ_API_KEY),
            "deepgram": bool(settings.DEEPGRAM_API_KEY),
        },
    }
