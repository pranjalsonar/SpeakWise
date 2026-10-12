// Own-profile API: view and update the logged-in user's details. Used by ProfilePage.
import type { User } from '@/core/types'
import { apiGet, apiPatch } from './client'
import { ENDPOINTS } from './endpoints'
import { toUser, type UserDto } from './userMapper'

export interface ProfileChanges {
  fullName?: string
  email?: string
}

/** The logged-in user's profile, fresh from the server. Throws ApiError. */
export async function getMyProfile(): Promise<User> {
  return toUser(await apiGet<UserDto>(ENDPOINTS.users.me))
}

/**
 * Update the logged-in user's name and/or email. Only the fields passed are sent.
 * Throws ApiError: 409 if the email belongs to another account, 422 if a value is invalid.
 */
export async function updateMyProfile(changes: ProfileChanges): Promise<User> {
  const body: Record<string, string> = {}
  if (changes.fullName !== undefined) body.full_name = changes.fullName.trim()
  if (changes.email !== undefined) body.email = changes.email.trim()
  return toUser(await apiPatch<UserDto>(ENDPOINTS.users.me, body))
}
