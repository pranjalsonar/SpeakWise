// Backend user shape + mapping to the app's User type. Shared by api.auth, api.users, api.admin.users.
import type { Role, User } from '@/core/types'
import { initialsOf } from '@/core/utils'

/** A user as the backend returns it (snake_case). Timestamps come from /users endpoints only. */
export interface UserDto {
  id: number
  email: string
  full_name: string | null
  role_id: number
  role: 'admin' | 'user'
  is_active: boolean
  created_at?: string
  updated_at?: string
}

const ROLE_MAP: Record<UserDto['role'], Role> = { admin: 'admin', user: 'student' }

export function toUser(dto: UserDto): User {
  const name = dto.full_name?.trim() || dto.email.split('@')[0] || 'SpeakWise User'
  return {
    name,
    firstName: name.split(' ')[0] ?? name,
    email: dto.email,
    initials: initialsOf(name),
    role: ROLE_MAP[dto.role] ?? 'student',
    joinedAt: dto.created_at,
  }
}
