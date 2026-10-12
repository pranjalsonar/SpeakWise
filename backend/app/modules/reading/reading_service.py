"""Reading material: pick a version the user hasn't recorded with, building new ones on demand.

Version choice for (user, topic):
1. the lowest version this user hasn't recorded a talk with;
2. else build the next version from pieces no earlier version used (advisory-locked per
   topic, so concurrent requests never build the same version twice);
3. else (no new material, or READING_MAX_VERSIONS reached) repeat the version they
   recorded longest ago, flagged `is_repeat`, with related topics to try instead.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.constants.difficulty import Difficulty
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException, UnprocessableException
from app.core.text import keywords
from app.integrations.wikipedia.client import (
    ArticleText,
    WikipediaClient,
    WikipediaError,
    WikipediaUnavailable,
    article_url,
    get_wikipedia_client,
)
from app.integrations.wikipedia.parser import parse_extract, total_words
from app.middleware.jwt_handler import TokenPayload
from app.models import ReadingMaterial, ReadingMaterialSource, Topic, TopicWikiSource, WikiArticle
from app.modules.reading import reading_repository as repo
from app.modules.reading.reading_builder import BuiltMaterial, SourceArticle, build_version
from app.modules.reading.reading_schemas import (
    ReadingMaterialResponse,
    ReadingSection,
    ReadingSource,
)
from app.modules.topics import topics_repository, topics_service
from app.modules.topics.topics_schemas import TopicResponse

logger = logging.getLogger("speakwise.reading")

MIN_SIMPLE_ARTICLE_WORDS = 300   # Beginner: use Simple English only if it has real content
MAX_SOURCES_PER_TOPIC = 8        # cap when adding related articles for more versions
RELATED_ARTICLES_PER_EXPANSION = 2
MAX_PARALLEL_FETCHES = 4         # concurrent article downloads (polite to Wikipedia)


# ---- Public API ----

def get_reading_material(
    db: Session, user: TokenPayload, topic_id: int, client: WikipediaClient | None = None
) -> ReadingMaterialResponse:
    topic = topics_service.get_active_topic(db, topic_id)
    recorded = repo.recorded_versions(db, user.user_id, topic.id)
    versions = repo.list_versions(db, topic.id)

    material = next((v for v in versions if v.id not in recorded), None)
    if material is None:
        material = build_next_version(db, topic, set(recorded), client)

    is_repeat = False
    if material is None:
        if not recorded:
            raise UnprocessableException(
                "We couldn't put together reading material for this topic. Try another topic"
            )
        # Every version recorded and nothing new to build: repeat the oldest-recorded one.
        oldest_id = min(recorded, key=recorded.get)
        material = next(v for v in repo.list_versions(db, topic.id) if v.id == oldest_id)
        is_repeat = True

    return _to_response(
        db,
        repo.get_material(db, material.id),
        topic,
        is_repeat=is_repeat,
        user_id=user.user_id,
    )


def build_next_version(
    db: Session,
    topic: Topic,
    exclude_ids: set[int] = frozenset(),
    client: WikipediaClient | None = None,
) -> ReadingMaterial | None:
    """Build and save the next version, or return an existing one not in `exclude_ids`.

    Returns None when no further distinct version can be built.
    """
    repo.lock_topic_for_build(db, topic.id)
    try:
        # Another request may have built a version while we waited for the lock.
        versions = repo.list_versions(db, topic.id)
        available = next((v for v in versions if v.id not in exclude_ids), None)
        if available or len(versions) >= settings.READING_MAX_VERSIONS:
            db.commit()
            return available

        client = client or get_wikipedia_client()
        used_keys = {key for v in versions for key in v.unit_keys}
        built = _build(db, topic, used_keys, client)

        # Not enough fresh material: pull in related articles once and try again.
        if built is None and len(topic.wiki_sources) < MAX_SOURCES_PER_TOPIC:
            if _add_related_sources(db, topic, client):
                built = _build(db, topic, used_keys, client)

        if built is None:
            db.commit()
            return None

        material = _save(db, topic, built, version_no=(versions[-1].version_no + 1) if versions else 1)
        db.commit()
        logger.info(
            "Built reading material topic=%s v%s (%s words, %s pieces)",
            topic.id, material.version_no, material.word_count, len(material.unit_keys),
        )
        return material
    except Exception:
        db.rollback()
        raise


# ---- Building ----

def _build(db: Session, topic: Topic, used_keys: set[str], client: WikipediaClient) -> BuiltMaterial | None:
    articles = ensure_articles(db, topic, client)
    if not articles:
        raise ServiceUnavailableException(
            "Couldn't load the Wikipedia articles for this topic. Please try again shortly"
        )

    terms = keywords(topic.title)
    for article in articles:
        terms |= keywords(article.title)

    return build_version(
        articles,
        terms,
        used_keys,
        target_words=settings.READING_TARGET_WORDS,
        min_words=min(800, settings.READING_TARGET_WORDS // 2),
    )


def _save(db: Session, topic: Topic, built: BuiltMaterial, version_no: int) -> ReadingMaterial:
    articles = {
        (a.lang, a.page_id): repo.get_article(db, a.lang, a.page_id) for a in built.articles
    }
    material = ReadingMaterial(
        topic_id=topic.id,
        version_no=version_no,
        lang=built.lang,
        content=built.content,
        unit_keys=built.unit_keys,
        word_count=built.word_count,
        read_minutes=built.read_minutes,
        sources=[
            ReadingMaterialSource(
                wiki_article_id=article.id,
                lang=article.lang,
                title=article.title,
                revision_id=article.revision_id,
                url=f"{article.url}?oldid={article.revision_id}",
            )
            for article in articles.values()
            if article is not None
        ],
    )
    return repo.add_material(db, material)


def ensure_articles(db: Session, topic: Topic, client: WikipediaClient) -> list[SourceArticle]:
    """Source articles for a topic from the cache, fetching/refreshing from Wikipedia as needed.

    Warm cache: no network at all. Missing/stale sources: one batched info request per
    language, then changed articles are fetched in parallel. Beginner topics use the
    Simple English counterpart (stored as its own source row) when it has real content.
    If Wikipedia is down, whatever is cached is still used.
    """
    stale_before = datetime.now(timezone.utc) - timedelta(days=settings.WIKI_CACHE_DAYS)
    prefer_simple = topic.difficulty == Difficulty.BEGINNER

    cache: dict[tuple[str, str], WikiArticle | None] = {
        (s.lang, s.page_title): repo.get_article_by_title(db, s.lang, s.page_title)
        for s in topic.wiki_sources
    }
    stale = [
        s
        for s in topic.wiki_sources
        if (article := cache[(s.lang, s.page_title)]) is None or article.fetched_at < stale_before
    ]
    if stale:
        try:
            _refresh_sources(db, topic, stale, cache, prefer_simple, client)
        except WikipediaUnavailable:
            logger.warning("Wikipedia unavailable; building topic %s from cache only", topic.id)

    return _pick_articles(topic, cache, prefer_simple)


def _pick_articles(
    topic: Topic, cache: dict[tuple[str, str], WikiArticle | None], prefer_simple: bool
) -> list[SourceArticle]:
    """One article per source rank (Simple English for Beginner when substantial), no duplicates."""
    by_rank: dict[int, dict[str, TopicWikiSource]] = {}
    for source in topic.wiki_sources:
        by_rank.setdefault(source.rank, {})[source.lang] = source

    articles: list[SourceArticle] = []
    seen: set[tuple[str, int]] = set()
    for rank in sorted(by_rank):
        options = by_rank[rank]
        article = None
        if prefer_simple and "simple" in options:
            simple = cache.get(("simple", options["simple"].page_title))
            if simple and simple.word_count >= MIN_SIMPLE_ARTICLE_WORDS:
                article = simple
        if article is None and "en" in options:
            article = cache.get(("en", options["en"].page_title))
        if not article or not article.sections or (article.lang, article.page_id) in seen:
            continue
        seen.add((article.lang, article.page_id))
        articles.append(
            SourceArticle(
                rank=len(articles),
                lang=article.lang,
                page_id=article.page_id,
                title=article.title,
                sections=article.sections,
            )
        )
    return articles


def _refresh_sources(
    db: Session,
    topic: Topic,
    stale: list[TopicWikiSource],
    cache: dict[tuple[str, str], WikiArticle | None],
    prefer_simple: bool,
    client: WikipediaClient,
) -> None:
    """Re-validate stale/missing sources and fetch what changed. Updates `cache` in place."""
    to_fetch: list[tuple[str, str]] = []  # (lang, title)

    for lang in sorted({s.lang for s in stale}):
        group = [s for s in stale if s.lang == lang]
        with_simple = prefer_simple and lang == "en"
        infos = client.page_info(lang, [s.page_title for s in group], with_simple_title=with_simple)

        for source in group:
            rank = source.rank
            info = infos.get(source.page_title)
            if info is None or info.is_disambiguation:
                logger.warning("Source %r is missing or a disambiguation page", source.page_title)
                continue
            key = _rename_source(topic, source, info.title)
            if key is None:
                continue  # duplicate of another source
            existing = cache.get(key) or repo.get_article(db, lang, info.page_id)
            if existing and existing.revision_id == info.revision_id:
                repo.touch_article(db, existing)
                cache[key] = existing
            else:
                to_fetch.append(key)

            if with_simple and info.simple_title:
                simple_key = _ensure_simple_source(topic, rank, info.simple_title)
                if cache.get(simple_key) is None:
                    cached_simple = repo.get_article_by_title(db, *simple_key)
                    if cached_simple:
                        cache[simple_key] = cached_simple
                    else:
                        to_fetch.append(simple_key)

    texts = _fetch_parallel(client, to_fetch)
    for (lang, title), text in zip(to_fetch, texts):
        if text is None:
            continue
        article = _store(db, lang, text)
        cache[(lang, title)] = article
        if text.title != title:  # the title redirected: point the source at the canonical one
            source = next((s for s in topic.wiki_sources if s.lang == lang and s.page_title == title), None)
            if source and _rename_source(topic, source, text.title):
                cache[(lang, text.title)] = article


def _rename_source(topic: Topic, source: TopicWikiSource, canonical: str) -> tuple[str, str] | None:
    """Store the canonical title so the cache hits next time.

    If another source of this topic already points at that article (both redirect to it),
    the duplicate is removed and None is returned.
    """
    if canonical != source.page_title:
        if any(
            s is not source and s.lang == source.lang and s.page_title == canonical
            for s in topic.wiki_sources
        ):
            topic.wiki_sources.remove(source)
            return None
        source.page_title = canonical
    return source.lang, canonical


def _ensure_simple_source(topic: Topic, rank: int, title: str) -> tuple[str, str]:
    """Remember the Simple English counterpart as a source row at the same rank."""
    existing = next(
        (s for s in topic.wiki_sources if s.lang == "simple" and (s.page_title == title or s.rank == rank)),
        None,
    )
    if existing is None:
        topic.wiki_sources.append(TopicWikiSource(rank=rank, lang="simple", page_title=title))
        return "simple", title
    return "simple", existing.page_title


def _fetch_parallel(client: WikipediaClient, items: list[tuple[str, str]]) -> list[ArticleText | None]:
    """Fetch full article texts concurrently (the API serves one full extract per request)."""
    if not items:
        return []

    def fetch(item: tuple[str, str]) -> ArticleText | None:
        try:
            return client.article_text(*item)
        except WikipediaError as exc:
            logger.warning("Couldn't fetch %r: %s", item, exc)
            return None

    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_FETCHES, len(items))) as pool:
        return list(pool.map(fetch, items))


def _store(db: Session, lang: str, text: ArticleText) -> WikiArticle:
    sections = parse_extract(text.extract)
    return repo.upsert_article(
        db,
        {
            "lang": lang,
            "page_id": text.page_id,
            "title": text.title,
            "revision_id": text.revision_id,
            "url": article_url(lang, text.title),
            "description": (text.description or "")[:500] or None,
            "sections": sections,
            "word_count": total_words(sections),
        },
    )


def _add_related_sources(db: Session, topic: Topic, client: WikipediaClient) -> bool:
    """Add a couple of related articles (morelike) to the topic for more distinct versions."""
    if not topic.wiki_sources:
        return False
    primary = min(topic.wiki_sources, key=lambda s: s.rank)
    try:
        hits = client.related("en", primary.page_title, limit=6)
    except WikipediaError:
        return False

    existing = {s.page_title for s in topic.wiki_sources}
    next_rank = max(s.rank for s in topic.wiki_sources) + 1
    added = 0
    for hit in hits:
        if hit.title in existing or hit.title.startswith("List of") or hit.word_count < 400:
            continue
        topic.wiki_sources.append(TopicWikiSource(rank=next_rank + added, lang="en", page_title=hit.title))
        added += 1
        if added == RELATED_ARTICLES_PER_EXPANSION:
            break
    db.flush()
    return added > 0


# ---- Response ----

def _to_response(
    db: Session, material: ReadingMaterial, topic: Topic, *, is_repeat: bool, user_id: int
) -> ReadingMaterialResponse:
    content = material.content
    sources = [
        ReadingSource(title=s.title, url=s.url, lang=s.lang, revision_id=s.revision_id)
        for s in material.sources
    ]
    site = "Simple English Wikipedia" if material.lang == "simple" else "Wikipedia"
    titles = ", ".join(f'"{s.title}"' for s in sources)
    return ReadingMaterialResponse(
        id=material.id,
        topic=TopicResponse.from_model(topic, recorded=topics_repository.has_recorded(db, user_id, topic.id)),
        version=material.version_no,
        is_repeat=is_repeat,
        lang=material.lang,
        summary=content["summary"],
        key_points=content["keyPoints"],
        sections=[ReadingSection(**s) for s in content["sections"]],
        word_count=material.word_count,
        read_minutes=material.read_minutes,
        sources=sources,
        attribution=f"Adapted from {site} articles {titles}, licensed under CC BY-SA 4.0.",
        related_topics=topics_service.related_topics(db, user_id, topic) if is_repeat else [],
    )
