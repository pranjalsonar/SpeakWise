"""Reading material shared with the mobile app (mobile/src/content/articles.json)."""
import json
import re
from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def _articles() -> dict[str, dict]:
    data = json.loads(settings.ARTICLES_FILE.read_text(encoding="utf-8"))
    return {a["id"]: a for a in data["articles"]}


def get_article(topic_id: str) -> dict | None:
    return _articles().get(topic_id)


def plain_text(markdown: str) -> str:
    """Article body without markdown symbols, for embeddings and the LLM judge."""
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", markdown)
    text = re.sub(r"[*_`>]", "", text)
    return text.strip()
