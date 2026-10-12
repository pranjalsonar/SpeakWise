"""Topic suggestions (curated) and user-typed custom topics resolved against Wikipedia."""
import logging
import math
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants.difficulty import Difficulty
from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    ServiceUnavailableException,
    TooManyRequestsException,
    UnprocessableException,
)
from app.core.text import keywords, normalize_topic, stem
from app.integrations.wikipedia.client import (
    PageInfo,
    WikipediaClient,
    WikipediaUnavailable,
    get_wikipedia_client,
)
from app.middleware.jwt_handler import TokenPayload
from app.models import Topic, TopicWikiSource
from app.modules.topics import topics_repository as repo
from app.modules.topics.topics_schemas import (
    CustomTopicResponse,
    DailyTopicResponse,
    SuggestTopicResponse,
    TopicResponse,
)

logger = logging.getLogger("speakwise.topics")

DAILY_EPOCH = date(2026, 1, 1)
CUSTOM_SEARCH_LIMIT = 10
CUSTOM_MAX_SOURCES = 3
MIN_ARTICLE_WORDS = 400
WIKITEXT_BYTES_PER_WORD = 7      # rough size estimate for articles not in search results
RELATIVE_SCORE_CUTOFF = 0.65     # drop candidates scoring below 65% of the best one
_BRACKETS = re.compile(r"\(.*\)")                            # "K Street (Sacramento)"
_NUMBERED = re.compile(r"^\d|\b\d{4}\b|\b\d+(?:st|nd|rd|th)\b")  # "43rd Chess Olympiad", "2027 ..."


# ---- Curated topics ----

def suggest_topic(
    db: Session,
    user: TokenPayload,
    category: str | None,
    difficulty: str | None,
    exclude_id: int | None,
) -> SuggestTopicResponse:
    """A random curated topic the user hasn't recorded; falls back to the oldest recorded one."""
    category_id = _category_id(db, category)
    level = _difficulty(difficulty)

    topic = repo.random_unrecorded_curated(db, user.user_id, category_id, level, exclude_id)
    if topic:
        return SuggestTopicResponse(topic=TopicResponse.from_model(topic), all_recorded=False)

    topic = repo.least_recently_recorded_curated(db, user.user_id, category_id, level, exclude_id)
    if topic is None:
        raise NotFoundException("No topics match these filters")
    return SuggestTopicResponse(
        topic=TopicResponse.from_model(topic, recorded=True), all_recorded=True
    )


def daily_topic(db: Session, user: TokenPayload) -> DailyTopicResponse:
    """Same topic for everyone each day: a fixed rotation through active curated topics."""
    count = repo.count_active_curated(db)
    if count == 0:
        raise NotFoundException("No topics available yet")

    today = repo.local_today(db, settings.REPORTING_TIMEZONE)
    topic = repo.curated_topic_at(db, (today - DAILY_EPOCH).days % count)
    return DailyTopicResponse(
        date=today,
        topic=TopicResponse.from_model(topic, repo.has_recorded(db, user.user_id, topic.id)),
    )


def get_topic(db: Session, user: TokenPayload, topic_id: int) -> TopicResponse:
    topic = get_active_topic(db, topic_id)
    return TopicResponse.from_model(topic, repo.has_recorded(db, user.user_id, topic.id))


def get_active_topic(db: Session, topic_id: int) -> Topic:
    topic = repo.get_topic(db, topic_id)
    if topic is None or not topic.is_active:
        raise NotFoundException("Topic not found")
    return topic


def related_topics(db: Session, user_id: int, topic: Topic, limit: int = 3) -> list[TopicResponse]:
    return [TopicResponse.from_model(t) for t in repo.related_unrecorded_curated(db, user_id, topic, limit)]


# ---- Custom topics ----

def create_custom_topic(
    db: Session,
    user: TokenPayload,
    text: str,
    client: WikipediaClient | None = None,
) -> CustomTopicResponse:
    """Find or create a topic for user-typed text, backed by matching Wikipedia articles.

    Re-typing an existing topic (any wording that normalizes the same) reuses it and
    doesn't count against the hourly limit.
    """
    try:
        normalized = normalize_topic(text)
    except ValueError:
        raise UnprocessableException("Describe the topic in a few meaningful words")

    existing = repo.get_topic_by_key(db, normalized.key)
    if existing:
        if not existing.is_active:
            raise UnprocessableException("This topic isn't available")
        return CustomTopicResponse(
            topic=TopicResponse.from_model(existing, repo.has_recorded(db, user.user_id, existing.id)),
            created=False,
        )

    since = datetime.now(timezone.utc) - timedelta(hours=1)
    if repo.count_custom_created_since(db, user.user_id, since) >= settings.CUSTOM_TOPICS_PER_HOUR:
        raise TooManyRequestsException(
            f"You can add up to {settings.CUSTOM_TOPICS_PER_HOUR} new topics per hour. "
            "Try one of the suggested topics, or try again later"
        )

    client = client or get_wikipedia_client()
    try:
        sources, description, suggestion = _find_articles(client, normalized.search_query)
    except WikipediaUnavailable:
        raise ServiceUnavailableException(
            "Couldn't reach Wikipedia to look up this topic. Please try again shortly"
        )

    if not sources:
        terms = sorted(keywords(normalized.search_query))
        raise UnprocessableException(
            "We couldn't find enough material on this topic. Try different wording",
            extra={
                "suggestion": suggestion,
                "related_topics": [
                    TopicResponse.from_model(t).model_dump()
                    for t in repo.curated_matching_terms(db, terms, limit=3)
                ],
            },
        )

    topic = Topic(
        title=normalized.title[:255],
        teaser=(description or "")[:500] or None,
        difficulty=Difficulty.INTERMEDIATE,
        source=repo.CUSTOM,
        normalized_key=normalized.key,
        created_by_user_id=user.user_id,
        wiki_sources=[
            TopicWikiSource(rank=rank, lang="en", page_title=title)
            for rank, title in enumerate(sources)
        ],
    )
    db.add(topic)
    try:
        db.commit()
    except IntegrityError:
        # Someone created the same topic a moment ago: use theirs.
        db.rollback()
        topic = repo.get_topic_by_key(db, normalized.key)
        if topic is None:
            raise
        return CustomTopicResponse(topic=TopicResponse.from_model(topic), created=False)

    topic = repo.get_topic(db, topic.id)
    logger.info("Custom topic %s created from %r -> %s", topic.id, text, sources)
    return CustomTopicResponse(topic=TopicResponse.from_model(topic), created=True)


def _find_articles(client: WikipediaClient, query: str) -> tuple[list[str], str | None, str | None]:
    """Pick the best Wikipedia articles for a typed topic (2 requests: search + batched info).

    Candidates are full-text search hits plus exact-title matches for the phrase and its
    word pairs (broad articles like "Chess" or "Homeschooling" often rank low in search
    for a question). Each is scored on title coverage/precision, snippet coverage,
    exact match, size and whether it contains the topic's subject; junk-looking titles
    (years, ordinals, brackets, "List of") are penalised or dropped. Candidates far below
    the best are discarded so weak matches don't pad the sources.

    Returns (canonical titles best first, description of the best one, "did you mean").
    """
    words = query.split()
    terms = keywords(query)
    if not terms:
        return [], None, None
    subject = next((stem(w) for w in words if stem(w) in terms), None)

    hits, suggestion = client.search("en", query, CUSTOM_SEARCH_LIMIT)
    hit_by_title = {hit.title: (position, hit) for position, hit in enumerate(hits)}
    phrase_titles = _phrase_titles(words)
    infos = client.page_info("en", list(dict.fromkeys([h.title for h in hits] + phrase_titles)))

    best: dict[str, tuple[float, PageInfo]] = {}  # canonical title -> (score, info)
    for requested, info in infos.items():
        if info.is_disambiguation or info.title.startswith("List of"):
            continue
        position, hit = hit_by_title.get(requested, (None, None))
        title_terms = keywords(info.title)
        matched = len(terms & title_terms)
        coverage = matched / len(terms)
        precision = matched / max(1, len(title_terms))
        snippet = len(terms & keywords(hit.snippet)) / len(terms) if hit else coverage
        words_estimate = hit.word_count if hit else info.length // WIKITEXT_BYTES_PER_WORD

        if words_estimate < MIN_ARTICLE_WORDS or (matched == 0 and snippet < 0.75):
            continue

        score = (
            2.5 * coverage
            + 2.0 * precision * coverage
            + 1.5 * snippet
            + (1.0 if requested in phrase_titles else 0.0)
            + (0.6 if subject and subject in title_terms else 0.0)
            + 0.4 * math.log10(max(words_estimate, 10))
            - (0.1 * position if position is not None else 0.3)
            - (1.0 if _BRACKETS.search(info.title) else 0.0)
            - (0.8 if _NUMBERED.search(info.title) else 0.0)
        )
        if info.title not in best or score > best[info.title][0]:
            best[info.title] = (score, info)

    if not best:
        return [], None, suggestion

    ranked = sorted(best.values(), key=lambda item: item[0], reverse=True)
    cutoff = ranked[0][0] * RELATIVE_SCORE_CUTOFF
    chosen = [info for score, info in ranked if score >= cutoff][:CUSTOM_MAX_SOURCES]
    return [info.title for info in chosen], chosen[0].description, suggestion


def _phrase_titles(words: list[str]) -> list[str]:
    """Possible exact article titles: the whole phrase, word pairs, and single words for short topics."""
    grams = [" ".join(words)]
    grams += [" ".join(words[i:i + 2]) for i in range(len(words) - 1)]
    if len(words) <= 2:
        grams += words
    return list(dict.fromkeys(g[0].upper() + g[1:] for g in grams if g))


# ---- helpers ----

def _category_id(db: Session, name: str | None) -> int | None:
    if not name:
        return None
    category = repo.get_category_by_name(db, name)
    if category is None:
        raise UnprocessableException(f"Unknown category: {name}")
    return category.id


def _difficulty(label: str | None) -> int | None:
    if not label:
        return None
    try:
        return Difficulty.from_label(label)
    except KeyError:
        raise UnprocessableException(f"Unknown difficulty: {label}")
