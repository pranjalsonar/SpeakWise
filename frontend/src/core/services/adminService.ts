import {
  adminKpis,
  adminLastUpdated,
  adminRecentSessions,
  adminUsers,
  sessionsByCategory,
  sessionsPerWeek,
} from '../data/mockData'
import type {
  AdminKpi,
  AdminRecentSession,
  AdminUser,
  CategoryShare,
  UserStatus,
  WeeklyCount,
} from '../types'
import { sleep } from '../utils'

// In-memory "database" for the mock. Resets on page reload.
let users: AdminUser[] = [...adminUsers]
let nextId = users.length + 1

const initialActiveInList = adminUsers.filter((u) => u.status === 'Active').length
const initialListSize = adminUsers.length

export class AdminError extends Error {}

export const isUserInactive = (email: string) =>
  users.some((u) => u.email.toLowerCase() === email.toLowerCase() && u.status === 'Inactive')

export interface AdminDashboard {
  kpis: AdminKpi[]
  sessionsPerWeek: WeeklyCount[]
  sessionsByCategory: CategoryShare[]
  recentSessions: AdminRecentSession[]
  lastUpdated: string
}

/** Platform KPIs: base numbers from the mock, adjusted by status toggles and new users. */
export function computeKpis(list: AdminUser[]): AdminKpi[] {
  const activeDelta = list.filter((u) => u.status === 'Active').length - initialActiveInList
  const addedUsers = list.length - initialListSize
  return adminKpis.map((kpi) => {
    if (kpi.key === 'totalUsers') {
      return { ...kpi, value: kpi.value + addedUsers }
    }
    if (kpi.key === 'activeUsers') {
      const total = (adminKpis.find((k) => k.key === 'totalUsers')?.value ?? 0) + addedUsers
      const active = kpi.value + activeDelta
      return { ...kpi, value: active, delta: `${Math.round((active / total) * 100)}% of all users` }
    }
    return kpi
  })
}

export async function getDashboard(): Promise<AdminDashboard> {
  await sleep(400)
  return {
    kpis: computeKpis(users),
    sessionsPerWeek,
    sessionsByCategory,
    recentSessions: adminRecentSessions,
    lastUpdated: adminLastUpdated,
  }
}

export async function getUsers(): Promise<AdminUser[]> {
  await sleep(400)
  return [...users]
}

export async function setUserStatus(id: string, status: UserStatus): Promise<AdminUser[]> {
  users = users.map((u) => (u.id === id ? { ...u, status } : u))
  await sleep(250)
  return [...users]
}

export const isEmailTaken = (email: string) =>
  users.some((u) => u.email.toLowerCase() === email.trim().toLowerCase())

export async function addUser(input: {
  name: string
  email: string
  status: UserStatus
}): Promise<AdminUser[]> {
  await sleep(500)
  if (isEmailTaken(input.email)) {
    throw new AdminError('A user with this email already exists.')
  }
  const newUser: AdminUser = {
    id: `u${nextId++}`,
    name: input.name.trim(),
    email: input.email.trim().toLowerCase(),
    sessions: 0,
    lastActive: 'Never',
    joined: 'Today',
    status: input.status,
  }
  users = [newUser, ...users]
  return [...users]
}
