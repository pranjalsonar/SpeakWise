import { Redirect, useLocalSearchParams, useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import Animated from 'react-native-reanimated';

import { ChecklistStep } from '@/components/session/checklist-step';
import { DurationStep } from '@/components/session/duration-step';
import { ProcessingStep } from '@/components/session/processing-step';
import { ReadingStep } from '@/components/session/reading-step';
import { useDialog } from '@/components/ui/dialog';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingScreen } from '@/components/ui/loading-screen';
import { useToast } from '@/components/ui/toast';
import { Screen } from '@/components/ui/screen';
import { ENTER_FADE } from '@/constants/motion';
import { useSession } from '@/hooks/use-session';
import { useTheme } from '@/hooks/use-theme';
import type { SessionStage } from '@/types/models';
import { deleteRecording } from '@/utils/recordings';

const STEP_OF: Partial<Record<SessionStage, number>> = {
  reading: 1,
  choosing_duration: 2,
  ready_to_record: 3,
  recorded: 4,
  uploading: 4,
  analyzing: 4,
  failed: 4,
};

/**
 * One screen for the whole practice flow. It renders the step stored in SQLite, so reopening
 * the app (or this route) always returns the user to exactly where they left off.
 */
export default function SessionScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { session, topic, loading, update } = useSession(Number(id));
  const dialog = useDialog();
  const toast = useToast();

  if (loading) return <LoadingScreen message="Opening your session…" />;
  if (!session || !topic) {
    return (
      <Screen>
        <EmptyState icon="search-off" title="Session not found" message="It may have been deleted." />
      </Screen>
    );
  }
  if (session.stage === 'done') return <Redirect href={{ pathname: '/report/[id]', params: { id: String(session.id) } }} />;
  if (session.stage === 'abandoned') return <Redirect href="/" />;

  const leave = () => (router.canGoBack() ? router.back() : router.replace('/'));
  const busy = session.stage === 'uploading' || session.stage === 'analyzing';
  const onClose = () => {
    // Analysis keeps running on the server; the app picks it up again from Home.
    if (busy) return leave();
    dialog.show({
      icon: 'logout',
      title: 'Leave this session?',
      message: 'Your progress is saved. You can continue from Home any time.',
      actions: [
        { label: 'Leave for now', onPress: leave },
        {
          label: 'Abandon session',
          style: 'destructive',
          onPress: async () => {
            await update({ stage: 'abandoned' });
            deleteRecording(session.videoPath);
            router.replace('/');
            toast.show('Session abandoned', 'info');
          },
        },
        { label: 'Keep going', style: 'cancel' },
      ],
    });
  };

  const props = { session, topic, update, onClose };
  const step = STEP_OF[session.stage] ?? 1;
  return (
    <View style={[styles.root, { backgroundColor: theme.background }]}>
      {/* Keyed by step, so moving to the next step fades in, while upload → analysing →
          failed stay on one mounted ProcessingStep (it must not restart its work). */}
      <Animated.View key={step} entering={ENTER_FADE} style={styles.root}>
        {session.stage === 'reading' && <ReadingStep {...props} />}
        {session.stage === 'choosing_duration' && <DurationStep {...props} />}
        {session.stage === 'ready_to_record' && <ChecklistStep {...props} />}
        {(session.stage === 'recorded' || busy || session.stage === 'failed') && <ProcessingStep {...props} />}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
