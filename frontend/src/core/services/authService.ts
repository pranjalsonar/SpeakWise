// Mock registration until the backend has a register endpoint.
// Login uses the real backend: see src/api/api.auth.ts.
import { mockAccounts } from '../data/mockData'
import type { User } from '../types'
import { initialsOf, sleep } from '../utils'

export type AuthErrorCode = 'credentials' | 'inactive' | 'exists'

export class AuthError extends Error {
  readonly code: AuthErrorCode
  constructor(code: AuthErrorCode, message: string) {
    super(message)
    this.code = code
  }
}

const REGISTER_DELAY_MS = 900

export async function register(name: string, email: string, _password: string): Promise<User> {
  await sleep(REGISTER_DELAY_MS)
  const normalized = email.trim().toLowerCase()
  if (mockAccounts.some((a) => a.email === normalized)) {
    throw new AuthError('exists', 'An account with this email already exists.')
  }
  const trimmed = name.trim()
  return {
    name: trimmed,
    firstName: trimmed.split(' ')[0] ?? trimmed,
    email: normalized,
    initials: initialsOf(trimmed),
    role: 'student',
  }
}
