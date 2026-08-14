from pydantic import BaseModel


class TopicResponse(BaseModel):
    title: str
    category: str
    difficulty: str