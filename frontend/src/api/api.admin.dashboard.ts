// Admin dashboard API: KPIs, sessions per week, category split, recent sessions.
// Used by AdminDataProvider for AdminDashboardPage. Admin-only on the backend (403 otherwise).
import type { AdminDashboard, AdminKpi, Category } from '@/core/types'
import { formatTimeAgo } from '@/core/utils'
import { apiGet } from './client'
import { ENDPOINTS } from './endpoints'

// ---- Backend response shape (snake_case, as the API returns it) ----
interface DashboardKpisDto {
  total_users: number
  new_users_this_month: number
  active_users: number
  active_users_pct: number
  total_sessions: number
  sessions_this_week: number
  minutes_spoken: number
  avg_minutes_per_session: number | null
  average_score: number | null
  average_score_change_vs_last_month: number | null
}

interface AdminDashboardDto {
  generated_at: string
  timezone: string
  kpis: DashboardKpisDto
  sessions_per_week: { week_start: string; count: number }[]
  sessions_by_category: { category: string; count: number; pct: number }[]
  recent_sessions: {
    id: number
    user_name: string
    topic: string | null
    score: number
    created_at: string
  }[]
}

// ---- Mapping to the app's AdminDashboard type ----

/** 5.1 → "+5", -2.4 → "-2", 0 → "+0" */
const signed = (value: number) => {
  const rounded = Math.round(value)
  return rounded >= 0 ? `+${rounded}` : `${rounded}`
}

function toKpis(k: DashboardKpisDto): AdminKpi[] {
  return [
    {
      key: 'totalUsers',
      label: 'Total users',
      value: k.total_users,
      delta: `+${k.new_users_this_month} this month`,
    },
    {
      key: 'activeUsers',
      label: 'Active users',
      value: k.active_users,
      delta: `${Math.round(k.active_users_pct)}% of all users`,
    },
    {
      key: 'sessions',
      label: 'Talk sessions recorded',
      value: k.total_sessions,
      delta: `+${k.sessions_this_week} this week`,
    },
    {
      key: 'minutes',
      label: 'Minutes spoken',
      value: k.minutes_spoken,
      delta:
        k.avg_minutes_per_session === null
          ? 'No recordings yet'
          : `${k.avg_minutes_per_session} min per session`,
    },
    {
      key: 'avgScore',
      label: 'Average score',
      value: k.average_score === null ? null : Math.round(k.average_score),
      delta:
        k.average_score_change_vs_last_month === null
          ? 'No comparison yet'
          : `${signed(k.average_score_change_vs_last_month)} vs last month`,
    },
  ]
}

/** "2026-09-28" → "Sep 28" (parsed as a local date so it doesn't shift a day). */
const weekLabel = (isoDate: string) =>
  new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

/** "Oct 4, 9:51 PM" */
const updatedLabel = (iso: string) =>
  new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })

function toDashboard(dto: AdminDashboardDto): AdminDashboard {
  return {
    kpis: toKpis(dto.kpis),
    sessionsPerWeek: dto.sessions_per_week.map((w) => ({
      week: weekLabel(w.week_start),
      count: w.count,
    })),
    sessionsByCategory: dto.sessions_by_category.map((c) => ({
      category: c.category as Category,
      pct: Math.round(c.pct),
    })),
    recentSessions: dto.recent_sessions.map((s) => ({
      id: String(s.id),
      user: s.user_name,
      topic: s.topic ?? 'Untitled topic',
      score: Math.round(s.score),
      when: formatTimeAgo(new Date(s.created_at)),
    })),
    lastUpdated: updatedLabel(dto.generated_at),
  }
}

// ---- API calls ----

/** Everything the admin dashboard shows, in one request. Throws ApiError (403 for non-admins). */
export async function getDashboard(): Promise<AdminDashboard> {
  return toDashboard(await apiGet<AdminDashboardDto>(ENDPOINTS.adminDashboard.summary))
}
