import { useRouter } from 'expo-router';
import { useSQLiteContext } from 'expo-sqlite';
import { useCallback } from 'react';

import { useDialog } from '@/components/ui/dialog';
import { createSession, getActiveSession, updateSession } from '@/db/sessions';
import { getTopic } from '@/db/topics';
import { deleteRecording } from '@/utils/recordings';

/** Starts a session for a topic, asking first if another session is still unfinished. */
export function useStartSession() {
  const db = useSQLiteContext();
  const router = useRouter();
  const dialog = useDialog();

  return useCallback(
    async (topicId: string) => {
      const open = (id: number) => router.push({ pathname: '/session/[id]', params: { id: String(id) } });
      const startNew = async () => open(await createSession(db, topicId));

      const active = await getActiveSession(db);
      if (!active) return startNew();
      if (active.topicId === topicId && active.stage !== 'failed') return open(active.id);

      const title = (await getTopic(db, active.topicId))?.title ?? 'another topic';
      dialog.show({
        icon: 'pending-actions',
        title: 'Unfinished session',
        message: `You still have a session on "${title}". Continue it, or start this topic instead?`,
        actions: [
          { label: 'Continue it', onPress: () => open(active.id) },
          {
            label: 'Start new',
            style: 'destructive',
            onPress: async () => {
              await updateSession(db, active.id, { stage: 'abandoned' });
              deleteRecording(active.videoPath);
              await startNew();
            },
          },
          { label: 'Cancel', style: 'cancel' },
        ],
      });
    },
    [db, router, dialog]
  );
}
