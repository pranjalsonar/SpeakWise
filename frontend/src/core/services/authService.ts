import { adminProfile, loginCopy, mockAccounts, user as demoUser } from '../data/mockData'
import type { Role, User } from '../types'
import { initialsOf, isValidEmail, sleep } from '../utils'
import { isUserInactive } from './adminService'

export type AuthErrorCode = 'credentials' | 'inactive' | 'exists'

export class AuthError extends Error {
  readonly code: AuthErrorCode
  constructor(code: AuthErrorCode, message: string) {
    super(message)
    this.code = code
  }
}

const LOGIN_DELAY_MS = 900

/** "john.doe@x.com" → "John Doe" (only used for mock logins without a known profile). */
function nameFromEmail(email: string): string {
  const local = email.split('@')[0] ?? ''
  const words = local.split(/[._-]+/).filter(Boolean)
  const name = words.map((w) => w[0]!.toUpperCase() + w.slice(1)).join(' ')
  return name || 'SpeakWise User'
}

function buildUser(name: string, email: string, role: Role): User {
  return {
    name,
    firstName: name.split(' ')[0] ?? name,
    email,
    initials: initialsOf(name),
    role,
  }
}

function profileFor(email: string, role: Role): User {
  if (role === 'admin') return { ...adminProfile, role }
  if (email.toLowerCase() === demoUser.email) return { ...demoUser, role }
  return buildUser(nameFromEmail(email), email, role)
}

/**
 * Mock rules (from the handoff):
 * - Known mock accounts log in with their role (password must match).
 * - Any other valid email + password of 6+ chars succeeds. `admin@…` gets the admin role.
 * - Users marked Inactive in the admin list are refused.
 */
export async function login(email: string, password: string): Promise<User> {
  await sleep(LOGIN_DELAY_MS)
  const normalized = email.trim().toLowerCase()

  if (isUserInactive(normalized)) {
    throw new AuthError('inactive', loginCopy.errors.inactive)
  }

  const account = mockAccounts.find((a) => a.email === normalized)
  if (account) {
    if (account.password !== password) {
      throw new AuthError('credentials', loginCopy.errors.credentials)
    }
    return profileFor(normalized, account.role)
  }

  if (!isValidEmail(normalized) || password.length < 6) {
    throw new AuthError('credentials', loginCopy.errors.credentials)
  }
  const role: Role = normalized.startsWith('admin@') ? 'admin' : 'student'
  return profileFor(normalized, role)
}

export async function register(name: string, email: string, _password: string): Promise<User> {
  await sleep(LOGIN_DELAY_MS)
  const normalized = email.trim().toLowerCase()
  if (mockAccounts.some((a) => a.email === normalized)) {
    throw new AuthError('exists', 'An account with this email already exists.')
  }
  return buildUser(name.trim(), normalized, 'student')
}
