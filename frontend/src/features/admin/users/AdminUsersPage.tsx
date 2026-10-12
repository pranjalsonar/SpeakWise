import { useState } from 'react'
import { Plus } from 'lucide-react'
import * as usersApi from '@/api/api.admin.users'
import { ApiError } from '@/api/client'
import { AdminShell } from '@/components/layout/AdminShell'
import { Banner } from '@/components/ui/Banner'
import { Button } from '@/components/ui/Button'
import { SearchInput } from '@/components/ui/SearchInput'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Skeleton } from '@/components/ui/Skeleton'
import { useCurrentUser } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import type { AdminUser } from '@/core/types'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { AddUserDialog } from './AddUserDialog'
import { EditUserDialog } from './EditUserDialog'
import { useAdminUsers } from './useAdminUsers'
import { UserRow } from './UserRow'
import './AdminUsersPage.css'

const FILTERS = ['All', 'Active', 'Inactive'] as const
type Filter = (typeof FILTERS)[number]

const STATUS_FOR: Record<Filter, usersApi.UserStatusFilter | undefined> = {
  All: undefined,
  Active: 'active',
  Inactive: 'inactive',
}

export function AdminUsersPage() {
  const isDesktop = useIsDesktop()
  const me = useCurrentUser()
  const { showToast } = useToast()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Filter>('All')
  const list = useAdminUsers(query, STATUS_FOR[filter])

  // Dialogs remount with a fresh key each time they open, so forms start clean.
  const [addKey, setAddKey] = useState(0)
  const [addOpen, setAddOpen] = useState(false)
  const [editing, setEditing] = useState<AdminUser | null>(null)
  const [editKey, setEditKey] = useState(0)

  const isSelf = (user: AdminUser) => user.email === me.email

  const toggleActive = async (user: AdminUser, isActive: boolean) => {
    list.replaceUser({ ...user, isActive }) // optimistic
    try {
      list.replaceUser(await usersApi.updateUser(user.id, { isActive }))
      showToast(`${user.name} is now ${isActive ? 'active' : 'inactive'}.`)
    } catch (error) {
      list.replaceUser(user) // revert
      showToast(error instanceof ApiError ? error.message : 'Could not change the status.')
    }
  }

  const openAdd = () => {
    setAddKey((k) => k + 1)
    setAddOpen(true)
  }

  const openEdit = (user: AdminUser) => {
    setEditKey((k) => k + 1)
    setEditing(user)
  }

  const addButton = (
    <Button size={isDesktop ? 'md' : 'sm'} iconLeft={<Plus size={16} />} onClick={openAdd}>
      Add user
    </Button>
  )

  const users = list.users ?? []

  return (
    <AdminShell mobileTitle="Users" mobileAction={addButton}>
      <div className="admin-users">
        <header className="admin-users__header">
          <div className="admin-users__heading">
            <h1 className="admin-users__title">Users</h1>
            <p className="admin-users__subtitle">
              {list.counts ? `${list.counts.active} active` : '…'} · add people and control who can
              log in.
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
            {list.counts && `Showing ${users.length} of ${list.total} users`}
            {list.loading && list.users && ' · updating…'}
          </span>
        </div>

        {list.error && !list.users ? (
          <div className="admin-users__error">
            <Banner>Couldn't load users. {list.error.message}</Banner>
            <Button variant="secondary" onClick={list.reload}>
              Try again
            </Button>
          </div>
        ) : !list.users ? (
          <Skeleton height={420} radius={40} />
        ) : (
          <section className="admin-users__table" aria-label="Users" aria-busy={list.loading}>
            <div className="admin-users__head" aria-hidden="true">
              <span>User</span>
              <span>Sessions</span>
              <span>Last active</span>
              <span>Joined</span>
              <span>Status</span>
              <span />
            </div>
            {users.map((user) => (
              <UserRow
                key={user.id}
                user={user}
                isSelf={isSelf(user)}
                onToggleActive={(active) => void toggleActive(user, active)}
                onEdit={() => openEdit(user)}
              />
            ))}
            {users.length === 0 && (
              <p className="admin-users__empty">
                {query.trim() || filter !== 'All' ? 'No users match your search.' : 'No users yet.'}
              </p>
            )}
            {list.hasMore && (
              <Button
                variant="secondary"
                className="admin-users__more"
                loading={list.loadingMore}
                onClick={() => void list.loadMore()}
              >
                Load more
              </Button>
            )}
          </section>
        )}
      </div>

      <AddUserDialog
        key={`add-${addKey}`}
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={list.addUser}
      />
      {editing && (
        <EditUserDialog
          key={`edit-${editKey}`}
          open
          user={editing}
          isSelf={isSelf(editing)}
          onClose={() => setEditing(null)}
          onSaved={(updated) => {
            list.replaceUser(updated)
            setEditing(null)
            showToast(`${updated.name} was updated.`)
          }}
        />
      )}
    </AdminShell>
  )
}
