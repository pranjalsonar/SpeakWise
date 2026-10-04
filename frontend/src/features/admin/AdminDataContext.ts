import { createContext, useContext } from 'react'
import type { AdminDashboard } from '@/core/services/adminService'
import type { AdminKpi, AdminUser, UserStatus } from '@/core/types'

export interface AdminDataValue {
  users: AdminUser[] | undefined
  dashboard: AdminDashboard | undefined
  /** KPIs recomputed from the live user list, so status toggles and new users show up immediately. */
  kpis: AdminKpi[] | undefined
  setStatus: (id: string, status: UserStatus) => void
  /** Rejects with a message when the email is taken. */
  addUser: (input: { name: string; email: string; status: UserStatus }) => Promise<void>
}

export const AdminDataContext = createContext<AdminDataValue | null>(null)

export function useAdminData(): AdminDataValue {
  const ctx = useContext(AdminDataContext)
  if (!ctx) throw new Error('useAdminData must be used inside <AdminDataProvider>')
  return ctx
}
