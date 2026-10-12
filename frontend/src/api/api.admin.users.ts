// Admin user management API: list, create, update, reset password. Used by the admin Users screen.
// Admin-only on the backend (403 otherwise).
import type { AdminUser, AdminUserCounts, Role } from '@/core/types'
import { apiGet, apiPatch, apiPost } from './client'
import { ENDPOINTS } from './endpoints'
import { toUser, type UserDto } from './userMapper'

// ---- Backend response shapes (snake_case, as the API returns them) ----
interface AdminUserDto extends UserDto {
  created_at: string
  session_count: number
  last_login_at: string | null
  last_session_at: string | null
  last_active_at: string | null
}

interface UserListDto {
  items: AdminUserDto[]
  total: number
  skip: number
  limit: number
  counts: AdminUserCounts
}

// ---- Mapping ----
const ROLE_IDS: Record<Role, number> = { admin: 1, student: 2 }

function toAdminUser(dto: AdminUserDto): AdminUser {
  const { name, email, initials, role } = toUser(dto)
  return {
    id: dto.id,
    name,
    fullName: dto.full_name,
    email,
    initials,
    role,
    isActive: dto.is_active,
    sessions: dto.session_count,
    lastActiveAt: dto.last_active_at,
    joinedAt: dto.created_at,
  }
}

// ---- API calls ----

export type UserStatusFilter = 'active' | 'inactive'

export interface UserListQuery {
  search?: string
  status?: UserStatusFilter
  skip?: number
  /** Capped at 100 by the backend. */
  limit?: number
}

export interface UserListPage {
  users: AdminUser[]
  /** Users matching search/status. */
  total: number
  /** Across all users, ignoring search/status. */
  counts: AdminUserCounts
}

/** One page of users (newest first) with session stats. Throws ApiError. */
export async function listUsers(query: UserListQuery = {}): Promise<UserListPage> {
  const params = new URLSearchParams({
    skip: String(query.skip ?? 0),
    limit: String(query.limit ?? 50),
  })
  if (query.search?.trim()) params.set('search', query.search.trim())
  if (query.status) params.set('status', query.status)

  const data = await apiGet<UserListDto>(`${ENDPOINTS.adminUsers.list}?${params}`)
  return { users: data.items.map(toAdminUser), total: data.total, counts: data.counts }
}

export async function getUser(id: number): Promise<AdminUser> {
  return toAdminUser(await apiGet<AdminUserDto>(ENDPOINTS.adminUsers.byId(id)))
}

export interface NewUser {
  fullName: string
  email: string
  role: Role
  isActive: boolean
}

/**
 * Create an account. The backend generates a temporary password, returned only here.
 * Throws ApiError: 409 if the email is taken.
 */
export async function createUser(
  input: NewUser,
): Promise<{ user: AdminUser; temporaryPassword: string }> {
  const data = await apiPost<{ user: AdminUserDto; temporary_password: string }>(
    ENDPOINTS.adminUsers.list,
    {
      full_name: input.fullName.trim(),
      email: input.email.trim(),
      role_id: ROLE_IDS[input.role],
      is_active: input.isActive,
    },
  )
  return { user: toAdminUser(data.user), temporaryPassword: data.temporary_password }
}

export interface AdminUserChanges {
  fullName?: string
  email?: string
  role?: Role
  isActive?: boolean
}

/**
 * Update any user. Only the fields passed are sent.
 * Throws ApiError: 404 unknown user, 409 email taken, 403 if an admin tries to demote/deactivate themselves.
 */
export async function updateUser(id: number, changes: AdminUserChanges): Promise<AdminUser> {
  const body: Record<string, unknown> = {}
  if (changes.fullName !== undefined) body.full_name = changes.fullName.trim()
  if (changes.email !== undefined) body.email = changes.email.trim()
  if (changes.role !== undefined) body.role_id = ROLE_IDS[changes.role]
  if (changes.isActive !== undefined) body.is_active = changes.isActive
  return toAdminUser(await apiPatch<AdminUserDto>(ENDPOINTS.adminUsers.byId(id), body))
}

/** Replace a user's password with a new temporary one and return it. Throws ApiError. */
export async function resetPassword(id: number): Promise<string> {
  const data = await apiPost<{ temporary_password: string }>(ENDPOINTS.adminUsers.resetPassword(id))
  return data.temporary_password
}
