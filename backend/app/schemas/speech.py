from pydantic import BaseModel


class SpeechRequest(BaseModel):
    name: str
    speech: str