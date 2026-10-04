// Safe wrappers around Web Storage. Private mode or blocked storage must never crash the app.
type StorageKind = 'local' | 'session'

const store = (kind: StorageKind): Storage | null => {
  try {
    return kind === 'local' ? window.localStorage : window.sessionStorage
  } catch {
    return null
  }
}

export function readJson<T>(key: string, fallback: T, kind: StorageKind = 'local'): T {
  try {
    const raw = store(kind)?.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

export function writeJson(key: string, value: unknown, kind: StorageKind = 'local'): void {
  try {
    store(kind)?.setItem(key, JSON.stringify(value))
  } catch {
    // Storage full or unavailable: persistence is a convenience, ignore.
  }
}

export function removeKey(key: string, kind: StorageKind = 'local'): void {
  try {
    store(kind)?.removeItem(key)
  } catch {
    // ignore
  }
}

export const STORAGE_KEYS = {
  auth: 'sw.auth',
  preferences: 'sw.preferences',
  session: 'sw.session',
} as const
