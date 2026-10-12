from datetime import date, datetime

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_users: int
    new_users_this_month: int
    active_users: int
    active_users_pct: float               # 0-100, one decimal
    total_sessions: int
    sessions_this_week: int
    minutes_spoken: int
    avg_minutes_per_session: float | None  # null until a session has a duration
    average_score: float | None            # null until a session is scored
    average_score_change_vs_last_month: float | None  # this month's avg minus last month's


class WeeklySessionCount(BaseModel):
    week_start: date  # Monday, in the reporting timezone
    count: int


class CategorySessionShare(BaseModel):
    category: str
    count: int
    pct: float  # share of categorised sessions, 0-100, one decimal


class RecentSession(BaseModel):
    id: int
    user_name: str
    topic: str | None
    score: float
    created_at: datetime


class AdminDashboardResponse(BaseModel):
    generated_at: datetime
    timezone: str
    kpis: DashboardKpis
    sessions_per_week: list[WeeklySessionCount]  # oldest first, current week last
    sessions_by_category: list[CategorySessionShare]
    recent_sessions: list[RecentSession]
