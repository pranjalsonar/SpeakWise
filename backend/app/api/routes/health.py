from fastapi import APIRouter

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