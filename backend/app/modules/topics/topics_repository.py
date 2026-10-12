from datetime import date, datetime

from sqlalchemy import exists, func, or_, select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import TalkSession, Topic, TopicCategory

CURATED = "curated"
CUSTOM = "custom"


def _recorded_by(user_id: int):
    """EXISTS(a talk session by this user on the topic)."""
    return exists().where(TalkSession.user_id == user_id, TalkSession.topic_id == Topic.id)


def _curated(category_id: int | None, difficulty: int | None, exclude_id: int | None):
    conditions = [Topic.source == CURATED, Topic.is_active.is_(True)]
    if category_id is not None:
        conditions.append(Topic.category_id == category_id)
    if difficulty is not None:
        conditions.append(Topic.difficulty == difficulty)
    if exclude_id is not None:
        conditions.append(Topic.id != exclude_id)
    return conditions


def get_topic(db: Session, topic_id: int) -> Topic | None:
    return db.scalar(
        select(Topic)
        .options(joinedload(Topic.category), selectinload(Topic.wiki_sources))
        .where(Topic.id == topic_id)
    )


def get_topic_by_key(db: Session, key: str) -> Topic | None:
    return db.scalar(
        select(Topic).options(joinedload(Topic.category)).where(Topic.normalized_key == key)
    )


def get_category_by_name(db: Session, name: str) -> TopicCategory | None:
    return db.scalar(select(TopicCategory).where(func.lower(TopicCategory.name) == name.lower()))


def random_unrecorded_curated(
    db: Session, user_id: int, category_id: int | None, difficulty: int | None, exclude_id: int | None
) -> Topic | None:
    """A random active curated topic this user hasn't recorded a talk on."""
    return db.scalar(
        select(Topic)
        .options(joinedload(Topic.category))
        .where(*_curated(category_id, difficulty, exclude_id), ~_recorded_by(user_id))
        .order_by(func.random())
        .limit(1)
    )


def least_recently_recorded_curated(
    db: Session, user_id: int, category_id: int | None, difficulty: int | None, exclude_id: int | None
) -> Topic | None:
    """Fallback when every matching topic was recorded: the one recorded longest ago."""
    last_recorded = (
        select(func.max(TalkSession.created_at))
        .where(TalkSession.user_id == user_id, TalkSession.topic_id == Topic.id)
        .scalar_subquery()
    )
    return db.scalar(
        select(Topic)
        .options(joinedload(Topic.category))
        .where(*_curated(category_id, difficulty, exclude_id))
        .order_by(last_recorded.asc().nulls_first(), Topic.id)
        .limit(1)
    )


def local_today(db: Session, tz: str) -> date:
    return db.scalar(text("SELECT (now() AT TIME ZONE :tz)::date"), {"tz": tz})


def curated_topic_at(db: Session, offset: int) -> Topic | None:
    """The n-th active curated topic in a stable order (for the daily rotation)."""
    return db.scalar(
        select(Topic)
        .options(joinedload(Topic.category))
        .where(*_curated(None, None, None))
        .order_by(Topic.id)
        .offset(offset)
        .limit(1)
    )


def count_active_curated(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Topic).where(*_curated(None, None, None))) or 0


def has_recorded(db: Session, user_id: int, topic_id: int) -> bool:
    return bool(
        db.scalar(
            select(
                exists().where(TalkSession.user_id == user_id, TalkSession.topic_id == topic_id)
            )
        )
    )


def count_custom_created_since(db: Session, user_id: int, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Topic)
            .where(
                Topic.source == CUSTOM,
                Topic.created_by_user_id == user_id,
                Topic.created_at >= since,
            )
        )
        or 0
    )


def related_unrecorded_curated(
    db: Session, user_id: int, topic: Topic, limit: int
) -> list[Topic]:
    """Other curated topics (same category first) the user hasn't recorded."""
    same_category_first = (Topic.category_id == topic.category_id).desc()
    return list(
        db.scalars(
            select(Topic)
            .options(joinedload(Topic.category))
            .where(*_curated(None, None, topic.id), ~_recorded_by(user_id))
            .order_by(same_category_first.nulls_last(), func.random())
            .limit(limit)
        )
    )


def curated_matching_terms(db: Session, terms: list[str], limit: int) -> list[Topic]:
    """Curated topics whose normalized key contains any of the terms (for 'did you mean')."""
    if not terms:
        return []
    return list(
        db.scalars(
            select(Topic)
            .options(joinedload(Topic.category))
            .where(
                *_curated(None, None, None),
                or_(*[Topic.normalized_key.ilike(f"%{term}%") for term in terms]),
            )
            .limit(limit)
        )
    )
