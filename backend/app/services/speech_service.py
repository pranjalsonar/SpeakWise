from app.schemas.speech import SpeechRequest
from app.schemas.response import SpeechAnalysisResponse


def analyze_speech(request: SpeechRequest) -> SpeechAnalysisResponse:
    word_count = len(request.speech.split())

    return SpeechAnalysisResponse(
        message="Speech received successfully.",
        speaker=request.name,
        word_count=word_count
    )