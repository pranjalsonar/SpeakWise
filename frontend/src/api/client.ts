// The only place that calls fetch(). api.<module>.ts files build on these helpers.
import { clearAccessToken, getAccessToken, notifyUnauthorized } from './authToken'
import { API_CONFIG } from './config'

export class ApiError extends Error {
  /** HTTP status, or 0 when the server couldn't be reached / timed out. */
  readonly status: number
  /** Raw `detail` from the backend (string, or a list for 422 validation errors). */
  readonly detail: unknown
  /** The whole error response body, for endpoints that add fields next to `detail`. */
  readonly body: unknown

  constructor(status: number, message: string, detail?: unknown, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.body = body
  }

  get isNetworkError(): boolean {
    return this.status === 0
  }
}

const NETWORK_ERROR = "Can't reach the server. Check your connection and try again."
const TIMEOUT_ERROR = 'The server took too long to respond. Please try again.'
const GENERIC_ERROR = 'Something went wrong. Please try again.'

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  /** Send the bearer token (default true). Set false for public routes like login. */
  auth?: boolean
  /** Use a full URL path instead of prefixing API_CONFIG.prefix (e.g. "/health"). */
  skipPrefix?: boolean
  signal?: AbortSignal
}

function messageFrom(detail: unknown, status: number): string {
  if (typeof detail === 'string') return detail
  if (status === 422) return 'Some of the information sent was invalid.'
  return GENERIC_ERROR
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true, skipPrefix = false, signal } = options
  const url = `${API_CONFIG.baseUrl}${skipPrefix ? '' : API_CONFIG.prefix}${path}`

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const token = auth ? getAccessToken() : null
  if (token) headers.Authorization = `Bearer ${token}`

  const timeout = AbortSignal.timeout(API_CONFIG.timeoutMs)

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    })
  } catch (error) {
    if (signal?.aborted) throw error // caller cancelled; let them handle it
    const timedOut = error instanceof DOMException && error.name === 'TimeoutError'
    throw new ApiError(0, timedOut ? TIMEOUT_ERROR : NETWORK_ERROR)
  }

  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null)

  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail

    // Token missing/expired/revoked on a protected route: end the session app-wide.
    if (response.status === 401 && auth) {
      clearAccessToken()
      notifyUnauthorized()
    }

    throw new ApiError(response.status, messageFrom(detail, response.status), detail, data)
  }

  return data as T
}

export const apiGet = <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
  apiRequest<T>(path, { ...options, method: 'GET' })

export const apiPost = <T>(
  path: string,
  body?: unknown,
  options?: Omit<RequestOptions, 'method' | 'body'>,
) => apiRequest<T>(path, { ...options, method: 'POST', body })

export const apiPatch = <T>(
  path: string,
  body: unknown,
  options?: Omit<RequestOptions, 'method' | 'body'>,
) => apiRequest<T>(path, { ...options, method: 'PATCH', body })
