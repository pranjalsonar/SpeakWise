import type { SQLiteDatabase } from 'expo-sqlite';

import articlesFile from '@/content/articles.json';
import type { ArticlesFile } from '@/types/models';

const DATABASE_VERSION = 1;
const CONTENT_VERSION_KEY = 'content_version';

/** Passed to <SQLiteProvider onInit>. Runs schema migrations, then seeds/updates the topics. */
export async function initDatabase(db: SQLiteDatabase) {
  await migrateDbIfNeeded(db);
  await seedTopicsIfNeeded(db, articlesFile as ArticlesFile);
}

async function migrateDbIfNeeded(db: SQLiteDatabase) {
  const result = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
  let currentDbVersion = result?.user_version ?? 0;
  if (currentDbVersion >= DATABASE_VERSION) {
    return;
  }
  if (currentDbVersion === 0) {
    await db.execAsync(`
PRAGMA journal_mode = 'wal';
PRAGMA foreign_keys = ON;
CREATE TABLE profile (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  first_name TEXT NOT NULL,
  last_name TEXT,
  age INTEGER,
  gender TEXT,
  goal TEXT,
  created_at INTEGER NOT NULL
);
CREATE TABLE topics (
  id TEXT PRIMARY KEY NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  level TEXT NOT NULL,
  read_minutes INTEGER NOT NULL,
  summary TEXT NOT NULL,
  talking_points TEXT NOT NULL,
  body TEXT NOT NULL,
  word_count INTEGER NOT NULL,
  as_of TEXT
);
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id TEXT NOT NULL REFERENCES topics(id),
  stage TEXT NOT NULL,
  duration_sec INTEGER,
  reading_progress REAL NOT NULL DEFAULT 0,
  video_path TEXT,
  job_id TEXT,
  report TEXT,
  overall_score REAL,
  error TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX sessions_stage_idx ON sessions(stage);
CREATE TABLE settings (
  key TEXT PRIMARY KEY NOT NULL,
  value TEXT NOT NULL
);
`);
    currentDbVersion = 1;
  }
  // if (currentDbVersion === 1) {
  //   Add more migrations
  // }
  await db.execAsync(`PRAGMA user_version = ${DATABASE_VERSION}`);
}

/** Upserts bundled articles whenever articles.json has a newer version than the device. */
async function seedTopicsIfNeeded(db: SQLiteDatabase, file: ArticlesFile) {
  const row = await db.getFirstAsync<{ value: string }>(
    'SELECT value FROM settings WHERE key = ?',
    CONTENT_VERSION_KEY
  );
  if (row && Number(row.value) >= file.version) {
    return;
  }
  await db.withExclusiveTransactionAsync(async (txn) => {
    for (const a of file.articles) {
      await txn.runAsync(
        `INSERT OR REPLACE INTO topics
           (id, title, category, level, read_minutes, summary, talking_points, body, word_count, as_of)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        a.id,
        a.title,
        a.category,
        a.level,
        a.read_minutes,
        a.summary,
        JSON.stringify(a.talking_points),
        a.body,
        a.word_count,
        a.as_of ?? null
      );
    }
    await txn.runAsync(
      'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
      CONTENT_VERSION_KEY,
      String(file.version)
    );
  });
}
