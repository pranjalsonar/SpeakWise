from pydantic import BaseModel


class SpeechAnalysisResponse(BaseModel):
    message: str
    speaker: str
    word_count: int