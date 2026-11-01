/**
 * SpeakWise backend client. Upload a recording (POST /jobs), then poll GET /jobs/{id}.
 * Every failure becomes an ApiError with a stable `code` and a message safe to show users.
 */
import { createUploadTask, FileSystemUploadType } from 'expo-file-system/legacy';
import type { SQLiteDatabase } from 'expo-sqlite';

import { APP_TOKEN_KEY, BACKEND_URL_KEY, defaultBackendUrl } from '@/constants/config';
import { getSetting } from '@/db/settings';
import type { Report } from '@/types/report';

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status?: number
  ) {
    super(message);
  }
}

export type Health = {
  status: string;
  articles: number;
  access_key_required?: boolean;
  providers: { groq: boolean; deepgram: boolean };
};

/** Where the backend is and the optional access key it expects (Profile → Server). */
export type Backend = { url: string; token: string };

export type Job = {
  id: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  step: string | null;
  progress: number;
  topic_id: string;
  error: { code: string; message: string } | null;
  result: Report | null;
};

const NETWORK_MESSAGE =
  "Can't reach the SpeakWise server. Check your internet and the server address in Profile → Server.";

export async function resolveBackend(db: SQLiteDatabase): Promise<Backend> {
  const [url, token] = await Promise.all([getSetting(db, BACKEND_URL_KEY), getSetting(db, APP_TOKEN_KEY)]);
  return { url: (url || defaultBackendUrl()).replace(/\/+$/, ''), token: token ?? '' };
}

const authHeaders = (token: string): Record<string, string> => (token ? { 'X-App-Token': token } : {});

function toApiError(status: number, body: unknown): ApiError {
  const detail = (body as { detail?: { code?: string; message?: string } } | null)?.detail;
  if (detail?.code) return new ApiError(detail.code, detail.message ?? 'Request failed.', status);
  if (status === 429) return new ApiError('rate_limited', 'The server is busy. Please try again in a minute.', status);
  return new ApiError('server', `The server had a problem (error ${status}). Please try again.`, status);
}

async function request<T>(url: string, timeoutMs: number, token = ''): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { Accept: 'application/json', ...authHeaders(token) },
    });
    const body = await res.json().catch(() => null);
    if (!res.ok) throw toApiError(res.status, body);
    return body as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError('network', NETWORK_MESSAGE);
  } finally {
    clearTimeout(timer);
  }
}

// Generous timeout: a sleeping cloud deployment can take a while to wake up.
export const checkHealth = (backend: Backend) => request<Health>(`${backend.url}/health`, 20000);

export const getJob = (backend: Backend, jobId: string) =>
  request<Job>(`${backend.url}/jobs/${encodeURIComponent(jobId)}`, 15000, backend.token);

export function uploadRecording(opts: {
  backend: Backend;
  videoUri: string;
  topicId: string;
  firstName: string;
  clientRef: string;
  onProgress?: (fraction: number) => void;
}): { promise: Promise<Job>; cancel: () => void } {
  const task = createUploadTask(
    `${opts.backend.url}/jobs`,
    opts.videoUri,
    {
      httpMethod: 'POST',
      headers: authHeaders(opts.backend.token),
      uploadType: FileSystemUploadType.MULTIPART,
      fieldName: 'video',
      mimeType: 'video/mp4',
      parameters: { topic_id: opts.topicId, first_name: opts.firstName, client_ref: opts.clientRef },
    },
    (p) => opts.onProgress?.(p.totalBytesExpectedToSend ? p.totalBytesSent / p.totalBytesExpectedToSend : 0)
  );

  const promise = (async () => {
    let res;
    try {
      res = await task.uploadAsync();
    } catch {
      throw new ApiError('network', NETWORK_MESSAGE);
    }
    if (!res) throw new ApiError('cancelled', 'Upload cancelled.');
    let body: unknown = null;
    try {
      body = JSON.parse(res.body);
    } catch {
      // non-JSON error page
    }
    if (res.status >= 400) throw toApiError(res.status, body);
    return body as Job;
  })();

  return { promise, cancel: () => void task.cancelAsync().catch(() => undefined) };
}
