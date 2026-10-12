from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.dashboard import dashboard_repository as repo
from app.modules.dashboard.dashboard_schemas import (
    AdminDashboardResponse,
    CategorySessionShare,
    DashboardKpis,
    RecentSession,
    WeeklySessionCount,
)

WEEKS_SHOWN = 8
RECENT_SESSIONS_SHOWN = 5


def get_admin_dashboard(db: Session) -> AdminDashboardResponse:
    tz = settings.REPORTING_TIMEZONE
    periods = repo.get_periods(db, tz)

    return AdminDashboardResponse(
        generated_at=datetime.now(timezone.utc),
        timezone=tz,
        kpis=_kpis(db, periods),
        sessions_per_week=_sessions_per_week(db, tz, periods),
        sessions_by_category=_sessions_by_category(db),
        recent_sessions=_recent_sessions(db),
    )


def _kpis(db: Session, periods: repo.Periods) -> DashboardKpis:
    total_users = repo.count_users(db)
    active_users = repo.count_active_users(db)
    total_seconds, timed_sessions = repo.duration_totals(db)

    score_this_month = repo.average_score(db, start=periods.month_start)
    score_last_month = repo.average_score(
        db, start=periods.last_month_start, end=periods.month_start
    )
    overall_score = repo.average_score(db)

    return DashboardKpis(
        total_users=total_users,
        new_users_this_month=repo.count_users(db, since=periods.month_start),
        active_users=active_users,
        active_users_pct=_pct(active_users, total_users),
        total_sessions=repo.count_sessions(db),
        sessions_this_week=repo.count_sessions(db, since=periods.week_start),
        minutes_spoken=round(total_seconds / 60),
        avg_minutes_per_session=(
            round(total_seconds / 60 / timed_sessions, 1) if timed_sessions else None
        ),
        average_score=round(float(overall_score), 1) if overall_score is not None else None,
        average_score_change_vs_last_month=(
            round(float(score_this_month - score_last_month), 1)
            if score_this_month is not None and score_last_month is not None
            else None
        ),
    )


def _sessions_per_week(db: Session, tz: str, periods: repo.Periods) -> list[WeeklySessionCount]:
    first_week = periods.week_start - timedelta(weeks=WEEKS_SHOWN - 1)
    counts = repo.weekly_session_counts(db, tz, since=first_week)

    # Fill weeks with no sessions so the chart always has WEEKS_SHOWN bars.
    weeks = [
        periods.week_start_date - timedelta(weeks=offset)
        for offset in range(WEEKS_SHOWN - 1, -1, -1)
    ]
    return [WeeklySessionCount(week_start=week, count=counts.get(week, 0)) for week in weeks]


def _sessions_by_category(db: Session) -> list[CategorySessionShare]:
    rows = repo.category_session_counts(db)
    categorised = sum(count for _, count in rows)
    return [
        CategorySessionShare(category=name, count=count, pct=_pct(count, categorised))
        for name, count in rows
    ]


def _recent_sessions(db: Session) -> list[RecentSession]:
    return [
        RecentSession(
            id=row.id,
            user_name=row.full_name or row.email.split("@")[0],
            topic=row.topic,
            score=float(row.score),
            created_at=row.created_at,
        )
        for row in repo.recent_scored_sessions(db, RECENT_SESSIONS_SHOWN)
    ]


def _pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0
