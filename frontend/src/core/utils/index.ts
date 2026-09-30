import type { Topic } from '../types'

export const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export const isValidEmail = (email: string) => EMAIL_RE.test(email.trim())

/** Seconds → "m:ss" (e.g. 161 → "2:41"). */
export function formatClock(totalSeconds: number): string {
  const safe = Math.max(0, Math.ceil(totalSeconds))
  const minutes = Math.floor(safe / 60)
  const seconds = safe % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

/** "Priya Sharma" → "PS". */
export function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}

export function greetingFor(date: Date): string {
  const hour = date.getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export type PasswordScore = 0 | 1 | 2 | 3

/**
 * 1 point each: length ≥ 8; letters + numbers; (uppercase AND symbol) OR length ≥ 12.
 * Any non-empty password scores at least 1 (Weak) so the meter always shows.
 */
export function passwordStrength(password: string): PasswordScore {
  if (!password) return 0
  let score = 0
  if (password.length >= 8) score++
  if (/[a-z]/i.test(password) && /\d/.test(password)) score++
  if ((/[A-Z]/.test(password) && /[^A-Za-z0-9]/.test(password)) || password.length >= 12) score++
  return Math.max(1, score) as PasswordScore
}

/** Random topic from the pool, avoiding `excludeId` when possible. */
export function pickRandomTopic(pool: Topic[], excludeId?: string): Topic | undefined {
  const candidates = pool.length > 1 ? pool.filter((t) => t.id !== excludeId) : pool
  return candidates[Math.floor(Math.random() * candidates.length)]
}

export const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value))

export const formatNumber = (value: number) => value.toLocaleString('en-US')

/** "Sep 27, 2026" */
export const formatLongDate = (date: Date) =>
  date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
