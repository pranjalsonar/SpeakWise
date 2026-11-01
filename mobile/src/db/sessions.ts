import type { SQLiteDatabase } from 'expo-sqlite';

import type { Category, Session, SessionStage } from '@/types/models';
import type { Report } from '@/types/report';

type SessionRow = {
  id: number;
  topic_id: string;
  stage: SessionStage;
  duration_sec: number | null;
  reading_progress: number;
  video_path: string | null;
  job_id: string | null;
  report: string | null;
  overall_score: number | null;
  error: string | null;
  created_at: number;
  updated_at: number;
};

export type SessionPatch = Partial<
  Pick<Session, 'stage' | 'durationSec' | 'readingProgress' | 'videoPath' | 'jobId' | 'report' | 'overallScore' | 'error'>
>;

export type HistoryItem = {
  id: number;
  topicTitle: string;
  category: Category;
  stage: SessionStage;
  overallScore: number | null;
  /** Seconds actually spoken (from the report), else the chosen duration. */
  durationSec: number;
  createdAt: number;
};

export type PracticeStats = {
  sessions: number;
  minutesSpoken: number;
  /** Consecutive days (ending today or yesterday) with at least one finished session. */
  streakDays: number;
};

/** Stages the user can come back to. "failed" stays resumable so the upload can be retried. */
const RESUMABLE = `('reading','choosing_duration','ready_to_record','recorded','uploading','analyzing','failed')`;

const COLUMNS: Record<keyof SessionPatch, string> = {
  stage: 'stage',
  durationSec: 'duration_sec',
  readingProgress: 'reading_progress',
  videoPath: 'video_path',
  jobId: 'job_id',
  report: 'report',
  overallScore: 'overall_score',
  error: 'error',
};

function toSession(r: SessionRow): Session {
  return {
    id: r.id,
    topicId: r.topic_id,
    stage: r.stage,
    durationSec: r.duration_sec,
    readingProgress: r.reading_progress,
    videoPath: r.video_path,
    jobId: r.job_id,
    report: r.report ? (JSON.parse(r.report) as Report) : null,
    overallScore: r.overall_score,
    error: r.error,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export async function createSession(db: SQLiteDatabase, topicId: string): Promise<number> {
  const now = Date.now();
  const res = await db.runAsync(
    `INSERT INTO sessions (topic_id, stage, created_at, updated_at) VALUES (?, 'reading', ?, ?)`,
    topicId,
    now,
    now
  );
  return res.lastInsertRowId;
}

export async function getSession(db: SQLiteDatabase, id: number): Promise<Session | null> {
  const row = await db.getFirstAsync<SessionRow>('SELECT * FROM sessions WHERE id = ?', id);
  return row ? toSession(row) : null;
}

export async function getActiveSession(db: SQLiteDatabase): Promise<Session | null> {
  const row = await db.getFirstAsync<SessionRow>(
    `SELECT * FROM sessions WHERE stage IN ${RESUMABLE} ORDER BY updated_at DESC LIMIT 1`
  );
  return row ? toSession(row) : null;
}

export async function updateSession(db: SQLiteDatabase, id: number, patch: SessionPatch): Promise<void> {
  const entries = Object.entries(patch) as [keyof SessionPatch, unknown][];
  if (!entries.length) return;
  const sets = entries.map(([k]) => `${COLUMNS[k]} = ?`).join(', ');
  const values = entries.map(([k, v]) => (k === 'report' && v != null ? JSON.stringify(v) : (v as string | number | null)));
  await db.runAsync(`UPDATE sessions SET ${sets}, updated_at = ? WHERE id = ?`, ...values, Date.now(), id);
}

export async function listHistory(db: SQLiteDatabase): Promise<HistoryItem[]> {
  const rows = await db.getAllAsync<{
    id: number;
    title: string;
    category: Category;
    stage: SessionStage;
    overall_score: number | null;
    duration_sec: number | null;
    report: string | null;
    created_at: number;
  }>(
    `SELECT s.id, t.title, t.category, s.stage, s.overall_score, s.duration_sec, s.report, s.created_at
     FROM sessions s JOIN topics t ON t.id = s.topic_id
     WHERE s.stage IN ('done', 'failed')
     ORDER BY s.created_at DESC`
  );
  return rows.map((r) => {
    const spoken = r.report ? (JSON.parse(r.report) as Report).speech?.duration_sec : undefined;
    return {
      id: r.id,
      topicTitle: r.title,
      category: r.category,
      stage: r.stage,
      overallScore: r.overall_score,
      durationSec: Math.round(spoken ?? r.duration_sec ?? 0),
      createdAt: r.created_at,
    };
  });
}

const dayKey = (ms: number) => {
  const d = new Date(ms);
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
};

export function computeStats(items: HistoryItem[]): PracticeStats {
  const done = items.filter((i) => i.stage === 'done');
  const days = new Set(done.map((i) => dayKey(i.createdAt)));
  let streak = 0;
  const cursor = new Date();
  if (!days.has(dayKey(cursor.getTime()))) cursor.setDate(cursor.getDate() - 1); // today not practised yet
  while (days.has(dayKey(cursor.getTime()))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return {
    sessions: done.length,
    minutesSpoken: Math.round(done.reduce((s, i) => s + i.durationSec, 0) / 60),
    streakDays: streak,
  };
}

export async function getLatestDone(db: SQLiteDatabase): Promise<HistoryItem | null> {
  const items = await listHistory(db);
  return items.find((i) => i.stage === 'done') ?? null;
}

/** 1-based number of this session among completed sessions ("your report for session 3"). */
export async function sessionNumber(db: SQLiteDatabase, id: number): Promise<number> {
  const row = await db.getFirstAsync<{ n: number }>(
    `SELECT COUNT(*) AS n FROM sessions
     WHERE stage = 'done' AND created_at <= (SELECT created_at FROM sessions WHERE id = ?)`,
    id
  );
  return Math.max(1, row?.n ?? 1);
}

export async function deleteSession(db: SQLiteDatabase, id: number): Promise<void> {
  await db.runAsync('DELETE FROM sessions WHERE id = ?', id);
}

export async function deleteAllHistory(db: SQLiteDatabase): Promise<string[]> {
  const rows = await db.getAllAsync<{ video_path: string | null }>('SELECT video_path FROM sessions');
  await db.runAsync('DELETE FROM sessions');
  return rows.map((r) => r.video_path).filter((p): p is string => !!p);
}
