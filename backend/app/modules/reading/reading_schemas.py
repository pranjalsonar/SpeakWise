from pydantic import BaseModel

from app.modules.topics.topics_schemas import TopicResponse

WIKIPEDIA_LICENSE = "CC BY-SA 4.0"
WIKIPEDIA_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"


class ReadingSection(BaseModel):
    heading: str
    paragraphs: list[str]


class ReadingSource(BaseModel):
    title: str
    url: str           # permalink to the exact revision used
    lang: str
    revision_id: int


class ReadingMaterialResponse(BaseModel):
    id: int            # send this back when the talk session is recorded
    topic: TopicResponse
    version: int
    # True when the user has recorded every available version and this one is shown again.
    is_repeat: bool
    lang: str          # "en" | "simple"
    summary: str
    key_points: list[str]
    sections: list[ReadingSection]
    word_count: int
    read_minutes: int
    sources: list[ReadingSource]
    license: str = WIKIPEDIA_LICENSE
    license_url: str = WIKIPEDIA_LICENSE_URL
    attribution: str
    # Only when is_repeat: other topics the user hasn't recorded yet.
    related_topics: list[TopicResponse] = []
