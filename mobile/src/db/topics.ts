import type { SQLiteDatabase } from 'expo-sqlite';

import type { Category, Topic, TopicListItem } from '@/types/models';

type TopicRow = {
  id: string;
  title: string;
  category: Category;
  level: string;
  read_minutes: number;
  summary: string;
  talking_points: string;
  body: string;
  word_count: number;
  as_of: string | null;
};

type TopicListRow = Pick<TopicRow, 'id' | 'title' | 'category' | 'read_minutes' | 'summary'>;

const toListItem = (r: TopicListRow): TopicListItem => ({
  id: r.id,
  title: r.title,
  category: r.category,
  readMinutes: r.read_minutes,
  summary: r.summary,
});

/** Local search over seeded topics (title, category, summary). No network involved. */
export async function searchTopics(
  db: SQLiteDatabase,
  query = '',
  category: Category | null = null
): Promise<TopicListItem[]> {
  const like = `%${query.trim().replace(/[\\%_]/g, (c) => `\\${c}`)}%`;
  const rows = await db.getAllAsync<TopicListRow>(
    `SELECT id, title, category, read_minutes, summary FROM topics
     WHERE (title LIKE $q ESCAPE '\\' OR category LIKE $q ESCAPE '\\' OR summary LIKE $q ESCAPE '\\')
       AND ($category IS NULL OR category = $category)
     ORDER BY category, title`,
    { $q: like, $category: category }
  );
  return rows.map(toListItem);
}

export async function getTopic(db: SQLiteDatabase, id: string): Promise<Topic | null> {
  const r = await db.getFirstAsync<TopicRow>('SELECT * FROM topics WHERE id = ?', id);
  if (!r) return null;
  return {
    ...toListItem(r),
    level: r.level,
    talkingPoints: JSON.parse(r.talking_points) as string[],
    body: r.body,
    wordCount: r.word_count,
    asOf: r.as_of,
  };
}

export async function getRandomTopicId(db: SQLiteDatabase, excludeId?: string): Promise<string | null> {
  const row = await db.getFirstAsync<{ id: string }>(
    'SELECT id FROM topics WHERE id != ? ORDER BY RANDOM() LIMIT 1',
    excludeId ?? ''
  );
  return row?.id ?? null;
}

export async function countTopics(db: SQLiteDatabase): Promise<number> {
  const row = await db.getFirstAsync<{ n: number }>('SELECT COUNT(*) AS n FROM topics');
  return row?.n ?? 0;
}
