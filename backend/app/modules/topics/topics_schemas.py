from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.constants.difficulty import Difficulty
from app.models import Topic

CustomTopicText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120)
]


class TopicResponse(BaseModel):
    id: int
    title: str
    teaser: str | None
    category: str | None
    difficulty: str  # "Beginner" | "Intermediate" | "Advanced"
    source: str      # "curated" | "custom"
    recorded: bool   # has the current user already recorded a talk on it?

    @classmethod
    def from_model(cls, topic: Topic, recorded: bool = False) -> "TopicResponse":
        return cls(
            id=topic.id,
            title=topic.title,
            teaser=topic.teaser,
            category=topic.category.name if topic.category else None,
            difficulty=Difficulty(topic.difficulty).label,
            source=topic.source,
            recorded=recorded,
        )


class SuggestTopicResponse(BaseModel):
    topic: TopicResponse
    # True when the user has recorded every matching topic and this is a repeat.
    all_recorded: bool


class DailyTopicResponse(BaseModel):
    date: date
    topic: TopicResponse


class CustomTopicRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"text": "Should cities ban cars from downtown?"}},
    )

    text: CustomTopicText


class CustomTopicResponse(BaseModel):
    topic: TopicResponse
    created: bool  # False if an identical topic already existed
