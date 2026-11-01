import { useSQLiteContext } from 'expo-sqlite';
import { useCallback, useEffect, useState } from 'react';

import { getSession, updateSession, type SessionPatch } from '@/db/sessions';
import { getTopic } from '@/db/topics';
import type { Session, Topic } from '@/types/models';

/** Loads a session and its topic; `update` persists to SQLite first, then updates the UI. */
export function useSession(id: number) {
  const db = useSQLiteContext();
  const [session, setSession] = useState<Session | null>(null);
  const [topic, setTopic] = useState<Topic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const s = await getSession(db, id);
      const t = s ? await getTopic(db, s.topicId) : null;
      if (!cancelled) {
        setSession(s);
        setTopic(t);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [db, id]);

  const update = useCallback(
    async (patch: SessionPatch) => {
      await updateSession(db, id, patch);
      setSession((s) => (s ? { ...s, ...patch, updatedAt: Date.now() } : s));
    },
    [db, id]
  );

  return { session, topic, loading, update };
}
