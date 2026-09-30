import { useMemo, useState } from 'react'
import { Plus } from 'lucide-react'
import { AdminShell } from '@/components/layout/AdminShell'
import { Button } from '@/components/ui/Button'
import { SearchInput } from '@/components/ui/SearchInput'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Skeleton } from '@/components/ui/Skeleton'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { useAdminData } from '../AdminDataContext'
import { AddUserDialog } from './AddUserDialog'
import { UserRow } from './UserRow'
import './AdminUsersPage.css'

const FILTERS = ['All', 'Active', 'Inactive'] as const
type Filter = (typeof FILTERS)[number]

export function AdminUsersPage() {
  const isDesktop = useIsDesktop()
  const { users, setStatus } = useAdminData()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Filter>('All')
  const [addOpen, setAddOpen] = useState(false)

  const all = useMemo(() => users ?? [], [users])
  const activeCount = all.filter((u) => u.status === 'Active').length
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return all.filter(
      (u) =>
        (filter === 'All' || u.status === filter) &&
        (!q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)),
    )
  }, [all, query, filter])

  const addButton = (
    <Button
      size={isDesktop ? 'md' : 'sm'}
      iconLeft={<Plus size={16} />}
      onClick={() => setAddOpen(true)}
    >
      Add user
    </Button>
  )

  return (
    <AdminShell mobileTitle="Users" mobileAction={addButton}>
      <div className="admin-users">
        <header className="admin-users__header">
          <div className="admin-users__heading">
            <h1 className="admin-users__title">Users</h1>
            <p className="admin-users__subtitle">
              {activeCount} active · add people and control who can log in.
            </p>
          </div>
          {addButton}
        </header>

        <div className="admin-users__toolbar">
          <SearchInput
            label="Search users"
            value={query}
            onChange={setQuery}
            placeholder="Search name or email"
            className="admin-users__search"
          />
          <SegmentedControl
            label="Filter users"
            options={FILTERS}
            value={filter}
            onChange={setFilter}
            fullWidth={!isDesktop}
          />
          <span className="admin-users__count" aria-live="polite">
            Showing {visible.length} of {all.length} users
          </span>
        </div>

        {!users ? (
          <Skeleton height={420} radius={40} />
        ) : (
          <section className="admin-users__table" aria-label="Users">
            <div className="admin-users__head" aria-hidden="true">
              <span>User</span>
              <span>Sessions</span>
              <span>Last active</span>
              <span>Joined</span>
              <span>Status</span>
            </div>
            {visible.map((user) => (
              <UserRow
                key={user.id}
                user={user}
                onStatusChange={(status) => setStatus(user.id, status)}
              />
            ))}
            {visible.length === 0 && (
              <p className="admin-users__empty">No users match your search.</p>
            )}
          </section>
        )}
      </div>

      <AddUserDialog open={addOpen} onClose={() => setAddOpen(false)} />
    </AdminShell>
  )
}
