import { User as UserIcon } from 'lucide-react'
import { ROUTES } from '@/app/routes'
import { AdminShell } from '@/components/layout/AdminShell'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { useAdminData } from '../AdminDataContext'
import { AdminRecentSessions } from './AdminRecentSessions'
import { CategoryBars } from './CategoryBars'
import { KpiGrid } from './KpiGrid'
import { WeeklyBarChart } from './WeeklyBarChart'
import './AdminDashboardPage.css'

export function AdminDashboardPage() {
  const { dashboard, kpis } = useAdminData()

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

        {!dashboard || !kpis ? (
          <>
            <Skeleton height={120} radius={32} />
            <Skeleton height={300} radius={36} />
          </>
        ) : (
          <>
            <KpiGrid kpis={kpis} />
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
