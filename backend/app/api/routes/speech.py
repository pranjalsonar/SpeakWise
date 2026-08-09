from fastapi import APIRouter

from app.schemas.speech import SpeechRequest
from app.schemas.response import SpeechAnalysisResponse
from app.services.speech_service import analyze_speech

router = APIRouter()


@router.post(
    "/analyze",
    response_model=SpeechAnalysisResponse
)
def analyze(request: SpeechRequest):
    return analyze_speech(request)