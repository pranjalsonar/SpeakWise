// Reads API settings from frontend/.env (see .env.example).

const DEFAULT_TIMEOUT_MS = 15_000

function trimSlashes(value: string): string {
  return value.replace(/\/+$/, '')
}

const baseUrl = trimSlashes(import.meta.env.VITE_API_BASE_URL ?? '')

if (!baseUrl) {
  throw new Error('VITE_API_BASE_URL is not set. Copy frontend/.env.example to frontend/.env.')
}

const timeoutMs = Number(import.meta.env.VITE_API_TIMEOUT_MS)

export const API_CONFIG = {
  baseUrl,
  /** e.g. "/api/v1". Endpoints in endpoints.ts are relative to this. */
  prefix: trimSlashes(import.meta.env.VITE_API_PREFIX ?? '/api/v1'),
  timeoutMs: Number.isFinite(timeoutMs) && timeoutMs > 0 ? timeoutMs : DEFAULT_TIMEOUT_MS,
} as const
