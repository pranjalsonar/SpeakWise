// Stores the backend access token and tells the app when it stops being valid.
// Kept in sessionStorage: it's cleared when the tab closes and isn't shared with other tabs.
import { readJson, removeKey, STORAGE_KEYS, writeJson } from '@/lib/storage'

interface StoredToken {
  accessToken: string
  /** ISO date from the login response. */
  expiresAt: string
}

export function setAccessToken(accessToken: string, expiresAt: string): void {
  writeJson(STORAGE_KEYS.token, { accessToken, expiresAt } satisfies StoredToken, 'session')
}

export function clearAccessToken(): void {
  removeKey(STORAGE_KEYS.token, 'session')
}

function readToken(): StoredToken | null {
  return readJson<StoredToken | null>(STORAGE_KEYS.token, null, 'session')
}

/** Milliseconds until the stored token expires; 0 if missing or already expired. */
export function tokenTimeLeftMs(): number {
  const stored = readToken()
  if (!stored) return 0
  return Math.max(0, new Date(stored.expiresAt).getTime() - Date.now())
}

/** The token to send, or null if there is none or it has expired. */
export function getAccessToken(): string | null {
  const stored = readToken()
  return stored && tokenTimeLeftMs() > 0 ? stored.accessToken : null
}

// ---- "Session ended" notifications (401 from the API) ----
type Listener = () => void
const listeners = new Set<Listener>()

/** Subscribe to "the backend rejected our token". Returns an unsubscribe function. */
export function onUnauthorized(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function notifyUnauthorized(): void {
  listeners.forEach((listener) => listener())
}
