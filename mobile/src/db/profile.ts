import type { SQLiteDatabase } from 'expo-sqlite';

import type { Profile, ProfileInput } from '@/types/models';

type ProfileRow = {
  first_name: string;
  last_name: string | null;
  age: number | null;
  gender: string | null;
  goal: string | null;
  created_at: number;
};

export async function getProfile(db: SQLiteDatabase): Promise<Profile | null> {
  const row = await db.getFirstAsync<ProfileRow>('SELECT * FROM profile WHERE id = 1');
  if (!row) return null;
  return {
    firstName: row.first_name,
    lastName: row.last_name,
    age: row.age,
    gender: row.gender,
    goal: row.goal,
    createdAt: row.created_at,
  };
}

export async function saveProfile(db: SQLiteDatabase, input: ProfileInput): Promise<void> {
  await db.runAsync(
    `INSERT INTO profile (id, first_name, last_name, age, gender, goal, created_at)
     VALUES (1, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       first_name = excluded.first_name,
       last_name = excluded.last_name,
       age = excluded.age,
       gender = excluded.gender,
       goal = excluded.goal`,
    input.firstName,
    input.lastName,
    input.age,
    input.gender,
    input.goal,
    Date.now()
  );
}
