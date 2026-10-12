from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, cast, func, select, text
from sqlalchemy.orm import Session

from app.models import TalkSession, TalkSessionSummary, TopicCategory, User


@dataclass(frozen=True)
class Periods:
    """Period boundaries in the reporting timezone (computed by PostgreSQL)."""

    month_start: datetime       # start of this calendar month
    last_month_start: datetime  # start of last calendar month
    week_start: datetime        # Monday 00:00 of this week
    week_start_date: date       # same, as a local date (for weekly buckets)


def get_periods(db: Session, tz: str) -> Periods:
    row = db.execute(
        text(
            """
            SELECT
              date_trunc('month', now() AT TIME ZONE :tz) AT TIME ZONE :tz AS month_start,
              date_trunc('month', (now() AT TIME ZONE :tz) - interval '1 month') AT TIME ZONE :tz
                AS last_month_start,
              date_trunc('week', now() AT TIME ZONE :tz) AT TIME ZONE :tz AS week_start,
              date_trunc('week', now() AT TIME ZONE :tz)::date AS week_start_date
            """
        ),
        {"tz": tz},
    ).one()
    return Periods(**row._mapping)


# ---- Users ----

def count_users(db: Session, since: datetime | None = None) -> int:
    query = select(func.count()).select_from(User)
    if since is not None:
        query = query.where(User.created_at >= since)
    return db.scalar(query) or 0


def count_active_users(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0


# ---- Sessions ----

def count_sessions(db: Session, since: datetime | None = None) -> int:
    query = select(func.count()).select_from(TalkSession)
    if since is not None:
        query = query.where(TalkSession.created_at >= since)
    return db.scalar(query) or 0


def duration_totals(db: Session) -> tuple[int, int]:
    """(total seconds spoken, number of sessions that have a duration)."""
    total, count = db.execute(
        select(
            func.coalesce(func.sum(TalkSession.duration_seconds), 0),
            func.count(TalkSession.duration_seconds),
        )
    ).one()
    return int(total), int(count)


def average_score(
    db: Session, start: datetime | None = None, end: datetime | None = None
) -> Decimal | None:
    query = select(func.avg(TalkSession.score)).where(TalkSession.score.is_not(None))
    if start is not None:
        query = query.where(TalkSession.created_at >= start)
    if end is not None:
        query = query.where(TalkSession.created_at < end)
    return db.scalar(query)


def weekly_session_counts(db: Session, tz: str, since: datetime) -> dict[date, int]:
    """Session counts keyed by the (local) Monday of each week, from `since` onwards."""
    week = cast(func.date_trunc("week", func.timezone(tz, TalkSession.created_at)), Date)
    rows = db.execute(
        select(week.label("week"), func.count())
        .where(TalkSession.created_at >= since)
        .group_by(week)
    ).all()
    return {row[0]: row[1] for row in rows}


def category_session_counts(db: Session) -> list[tuple[str, int]]:
    """Every category with its session count (including zero), most sessions first."""
    count = func.count(TalkSession.id)
    rows = db.execute(
        select(TopicCategory.name, count)
        .outerjoin(TalkSession, TalkSession.category_id == TopicCategory.id)
        .group_by(TopicCategory.id, TopicCategory.name)
        .order_by(count.desc(), TopicCategory.id)
    ).all()
    return [(name, total) for name, total in rows]


def recent_scored_sessions(db: Session, limit: int):
    """Latest sessions that have a score, with the user and best-known topic title."""
    topic = func.coalesce(TalkSession.topic_title, TalkSessionSummary.topic_name)
    return db.execute(
        select(
            TalkSession.id,
            TalkSession.score,
            TalkSession.created_at,
            topic.label("topic"),
            User.full_name,
            User.email,
        )
        .join(User, User.id == TalkSession.user_id)
        .outerjoin(TalkSessionSummary, TalkSessionSummary.talk_session_id == TalkSession.id)
        .where(TalkSession.score.is_not(None))
        .order_by(TalkSession.created_at.desc())
        .limit(limit)
    ).all()
