from datetime import datetime
from typing import Literal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import TalkSession, User

StatusFilter = Literal["active", "inactive"]


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


# ---- Admin list: users + session stats ----

# Per-user session count and latest session time.
_session_stats = (
    select(
        TalkSession.user_id.label("user_id"),
        func.count(TalkSession.id).label("session_count"),
        func.max(TalkSession.created_at).label("last_session_at"),
    )
    .group_by(TalkSession.user_id)
    .subquery()
)


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _filters(search: str | None, status: StatusFilter | None) -> list:
    conditions = []

    if search:
        pattern = f"%{_escape_like(search.strip())}%"
        conditions.append(
            or_(User.full_name.ilike(pattern, escape="\\"), User.email.ilike(pattern, escape="\\"))
        )

    if status is not None:
        conditions.append(User.is_active.is_(status == "active"))

    return conditions


def list_users_with_stats(
    db: Session,
    *,
    search: str | None,
    status: StatusFilter | None,
    skip: int,
    limit: int,
) -> tuple[list[tuple[User, int, datetime | None]], int]:
    """(rows of (user, session_count, last_session_at), total matching), newest users first."""
    conditions = _filters(search, status)

    total = db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0
    rows = db.execute(
        select(
            User,
            func.coalesce(_session_stats.c.session_count, 0),
            _session_stats.c.last_session_at,
        )
        .options(joinedload(User.role))
        .outerjoin(_session_stats, _session_stats.c.user_id == User.id)
        .where(*conditions)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return [(user, count, last) for user, count, last in rows], total


def count_users_by_status(db: Session) -> tuple[int, int]:
    """(all users, active users)."""
    total, active = db.execute(
        select(func.count(), func.count(case((User.is_active.is_(True), 1))))
        .select_from(User)
    ).one()
    return total, active


def get_session_stats(db: Session, user_id: int) -> tuple[int, datetime | None]:
    count, last = db.execute(
        select(func.count(TalkSession.id), func.max(TalkSession.created_at)).where(
            TalkSession.user_id == user_id
        )
    ).one()
    return count, last


# ---- Writes ----

def add_user(db: Session, user: User) -> User:
    db.add(user)
    return save_user(db, user)


def save_user(db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user
