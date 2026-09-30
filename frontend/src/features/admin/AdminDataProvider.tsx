import { useCallback, useMemo, useState } from 'react'
import { Outlet } from 'react-router'
import { useAsync } from '@/core/hooks/useAsync'
import { adminService } from '@/core/services'
import type { AdminUser, UserStatus } from '@/core/types'
import { AdminDataContext, type AdminDataValue } from './AdminDataContext'

/** Shared admin state for /admin and /admin/users (rendered as the parent route). */
export function AdminDataProvider() {
  const { data: dashboard } = useAsync(() => adminService.getDashboard(), [])
  const { data: loadedUsers } = useAsync(() => adminService.getUsers(), [])
  // Local edits override the loaded list once the admin changes something.
  const [editedUsers, setEditedUsers] = useState<AdminUser[] | null>(null)
  const users = editedUsers ?? loadedUsers

  const setStatus = useCallback(
    (id: string, status: UserStatus) => {
      // Optimistic: flip locally right away, then persist (PATCH /users/:id with the real API).
      setEditedUsers((edited) =>
        (edited ?? loadedUsers ?? []).map((u) => (u.id === id ? { ...u, status } : u)),
      )
      void adminService.setUserStatus(id, status)
    },
    [loadedUsers],
  )

  const addUser = useCallback(
    async (input: { name: string; email: string; status: UserStatus }) => {
      setEditedUsers(await adminService.addUser(input))
    },
    [],
  )

  const value = useMemo<AdminDataValue>(
    () => ({
      users,
      dashboard,
      kpis: users ? adminService.computeKpis(users) : dashboard?.kpis,
      setStatus,
      addUser,
    }),
    [users, dashboard, setStatus, addUser],
  )

  return (
    <AdminDataContext.Provider value={value}>
      <Outlet />
    </AdminDataContext.Provider>
  )
}
