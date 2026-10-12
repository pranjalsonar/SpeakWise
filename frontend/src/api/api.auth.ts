// Auth API: login, logout, current user. Used by LoginPage and AuthProvider.
import type { User } from '@/core/types'
import { clearAccessToken, getAccessToken, setAccessToken } from './authToken'
import { apiGet, apiPost } from './client'
import { ENDPOINTS } from './endpoints'
import { toUser, type UserDto } from './userMapper'

// ---- Backend response shape (snake_case, as the API returns it) ----
interface LoginResponseDto {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  expires_at: string
  user: UserDto
}

// ---- API calls ----

/** Logs in, stores the access token, and returns the signed-in user. Throws ApiError. */
export async function login(email: string, password: string): Promise<User> {
  const data = await apiPost<LoginResponseDto>(
    ENDPOINTS.auth.login,
    { email: email.trim(), password },
    { auth: false },
  )
  setAccessToken(data.access_token, data.expires_at)
  return toUser(data.user)
}

/** Revokes the token on the server (best effort) and always clears it locally. */
export async function logout(): Promise<void> {
  try {
    if (getAccessToken()) await apiPost<{ message: string }>(ENDPOINTS.auth.logout)
  } catch {
    // Already expired/revoked or offline: the local logout still happens.
  } finally {
    clearAccessToken()
  }
}

/** The logged-in user's profile, fresh from the server. Throws ApiError (401 if signed out). */
export async function getCurrentUser(): Promise<User> {
  return toUser(await apiGet<UserDto>(ENDPOINTS.auth.me))
}
