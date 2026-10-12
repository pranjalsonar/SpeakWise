import { User as UserIcon } from 'lucide-react'
import { useState } from 'react'
import * as dashboardApi from '@/api/api.admin.dashboard'
import { ROUTES } from '@/app/routes'
import { AdminShell } from '@/components/layout/AdminShell'
import { Banner } from '@/components/ui/Banner'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { useAsync } from '@/core/hooks/useAsync'
import { AdminRecentSessions } from './AdminRecentSessions'
import { CategoryBars } from './CategoryBars'
import { KpiGrid } from './KpiGrid'
import { WeeklyBarChart } from './WeeklyBarChart'
import './AdminDashboardPage.css'

export function AdminDashboardPage() {
  // Fetched on every visit, so changes made on the Users page show up here.
  const [version, setVersion] = useState(0)
  const { data: dashboard, error: dashboardError } = useAsync(
    () => dashboardApi.getDashboard(),
    [version],
  )
  const reloadDashboard = () => setVersion((v) => v + 1)

  return (
    <AdminShell mobileTitle="Dashboard">
      <div className="admin-dash">
        <header className="admin-dash__header">
          <div className="admin-dash__heading">
            <h1 className="admin-dash__title">Dashboard</h1>
            <p className="admin-dash__subtitle">
              Platform activity · last updated {dashboard?.lastUpdated ?? '…'}
            </p>
          </div>
          <Button variant="secondary" to={ROUTES.adminUsers} iconLeft={<UserIcon size={16} />}>
            Manage users
          </Button>
        </header>

        {dashboardError && !dashboard ? (
          <div className="admin-dash__error">
            <Banner>Couldn't load the dashboard. {dashboardError.message}</Banner>
            <Button variant="secondary" onClick={reloadDashboard}>
              Try again
            </Button>
          </div>
        ) : !dashboard ? (
          <>
            <Skeleton height={120} radius={32} />
            <Skeleton height={300} radius={36} />
          </>
        ) : (
          <>
            <KpiGrid kpis={dashboard.kpis} />
            <div className="admin-dash__charts">
              <WeeklyBarChart weeks={dashboard.sessionsPerWeek} />
              <div className="admin-dash__categories">
                <CategoryBars shares={dashboard.sessionsByCategory} />
              </div>
            </div>
            <AdminRecentSessions sessions={dashboard.recentSessions} />
          </>
        )}
      </div>
    </AdminShell>
  )
}
