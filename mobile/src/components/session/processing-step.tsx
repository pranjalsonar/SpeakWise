import { MaterialIcons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
import { useSQLiteContext } from 'expo-sqlite';
import { useCallback, useEffect, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { css, useReducedMotion } from 'react-native-reanimated';

import { SessionHeader } from '@/components/session/session-header';
import type { StepProps } from '@/components/session/types';
import { ThemedText } from '@/components/themed-text';
import { Banner } from '@/components/ui/banner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ProgressBar } from '@/components/ui/progress-bar';
import { Screen } from '@/components/ui/screen';
import { Spinner } from '@/components/ui/spinner';
import { POLL_INTERVAL_MS } from '@/constants/config';
import { Radius, Spacing } from '@/constants/theme';
import { useProfile } from '@/context/profile-context';
import { useOnline } from '@/hooks/use-online';
import { useTheme } from '@/hooks/use-theme';
import { ApiError, checkHealth, getJob, resolveBackend, uploadRecording, type Backend } from '@/services/api';
import { deleteRecording, recordingExists } from '@/utils/recordings';

type View_ =
  | { kind: 'connecting' }
  | { kind: 'offline' }
  | { kind: 'uploading'; progress: number }
  | { kind: 'analyzing'; step: string | null; progress: number; reconnecting?: boolean }
  | { kind: 'error'; message: string; canRetry: boolean };

/** Handoff checklist; each item covers one or more backend job steps. */
const CHECKLIST: { label: string; steps: string[] }[] = [
  { label: 'Uploaded', steps: [] },
  { label: 'Watching body language', steps: ['queued', 'preparing', 'analysing'] },
  { label: 'Transcribing speech', steps: ['transcribing'] },
  { label: 'Analysing delivery', steps: ['measuring', 'checking_content', 'scoring'] },
  { label: 'Generating feedback', steps: ['writing_feedback'] },
];

/** Errors where uploading the same recording again cannot help. */
const FINAL_CODES = new Set(['no_speech', 'no_audio', 'too_long', 'too_short', 'invalid_file', 'too_large', 'unknown_topic']);
/** Errors meaning the server lost the job, so the recording should simply be uploaded again. */
const REUPLOAD_CODES = new Set(['interrupted', 'not_found']);

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function ProcessingStep({ session, topic, update, onClose }: StepProps) {
  const theme = useTheme();
  const reducedMotion = useReducedMotion();
  const db = useSQLiteContext();
  const router = useRouter();
  const online = useOnline();
  const { profile } = useProfile();
  const [view, setView] = useState<View_>(
    session.stage === 'failed'
      ? { kind: 'error', message: session.error ?? 'The analysis failed.', canRetry: true }
      : { kind: 'connecting' }
  );
  const running = useRef(false);
  const mounted = useRef(true);
  const cancelUpload = useRef<(() => void) | null>(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      cancelUpload.current?.();
    };
  }, []);

  const fail = useCallback(
    async (message: string, final: boolean) => {
      if (final) await update({ stage: 'failed', error: message });
      if (mounted.current) setView({ kind: 'error', message, canRetry: true });
    },
    [update]
  );

  const poll = useCallback(
    async (backend: Backend, jobId: string): Promise<'reupload' | void> => {
      let misses = 0;
      while (mounted.current) {
        try {
          const job = await getJob(backend, jobId);
          misses = 0;
          if (job.status === 'done' && job.result) {
            await update({ stage: 'done', report: job.result, overallScore: job.result.scores.overall, error: null });
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => undefined);
            router.replace({ pathname: '/report/[id]', params: { id: String(session.id) } });
            return;
          }
          if (job.status === 'failed') {
            const code = job.error?.code ?? 'internal';
            if (REUPLOAD_CODES.has(code)) return 'reupload';
            await fail(job.error?.message ?? 'The analysis failed.', true);
            return;
          }
          setView({ kind: 'analyzing', step: job.step, progress: job.progress });
        } catch (e) {
          if (e instanceof ApiError && REUPLOAD_CODES.has(e.code)) return 'reupload';
          if (e instanceof ApiError && e.code === 'unauthorized') {
            await fail(e.message, false);
            return;
          }
          misses += 1;
          setView((v) => (v.kind === 'analyzing' ? { ...v, reconnecting: true } : { kind: 'analyzing', step: null, progress: 0, reconnecting: true }));
          if (misses > 40) {
            await fail('Lost connection to the server. Your recording is saved; tap Try again when you are back online.', false);
            return;
          }
        }
        await sleep(POLL_INTERVAL_MS);
      }
    },
    [fail, router, session.id, update]
  );

  const run = useCallback(
    async (forceUpload = false) => {
      if (running.current) return;
      running.current = true;
      try {
        if (!online) {
          setView({ kind: 'offline' });
          return;
        }
        setView({ kind: 'connecting' });
        const backend = await resolveBackend(db);

        if (!forceUpload && session.jobId && session.stage === 'analyzing') {
          const outcome = await poll(backend, session.jobId);
          if (outcome !== 'reupload') return;
        }

        if (!recordingExists(session.videoPath)) {
          await fail('The recording file is missing. Please record again.', true);
          return;
        }
        try {
          await checkHealth(backend);
        } catch (e) {
          await fail((e as ApiError).message, false);
          return;
        }

        await update({ stage: 'uploading', jobId: null, error: null });
        setView({ kind: 'uploading', progress: 0 });
        const upload = uploadRecording({
          backend,
          videoUri: session.videoPath!,
          topicId: topic.id,
          firstName: profile?.firstName ?? '',
          clientRef: `s${session.id}-${session.createdAt}`,
          onProgress: (p) => mounted.current && setView({ kind: 'uploading', progress: p }),
        });
        cancelUpload.current = upload.cancel;
        let job;
        try {
          job = await upload.promise;
        } catch (e) {
          const err = e as ApiError;
          if (err.code === 'cancelled') return;
          await fail(err.message, FINAL_CODES.has(err.code));
          return;
        } finally {
          cancelUpload.current = null;
        }

        await update({ stage: 'analyzing', jobId: job.id });
        setView({ kind: 'analyzing', step: job.step, progress: job.progress });
        const outcome = await poll(backend, job.id);
        if (outcome === 'reupload') {
          running.current = false;
          await run(true);
        }
      } finally {
        running.current = false;
      }
    },
    [db, fail, online, poll, profile?.firstName, session, topic.id, update]
  );

  // Start (or resume) automatically, and again when the connection comes back.
  useEffect(() => {
    if (session.stage === 'failed') return;
    if (view.kind === 'connecting' || view.kind === 'offline') run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [online]);

  const retry = async () => {
    await update({ stage: 'recorded', error: null });
    run(true);
  };

  const recordAgain = async () => {
    cancelUpload.current?.();
    deleteRecording(session.videoPath);
    await update({ stage: 'ready_to_record', videoPath: null, jobId: null, error: null });
  };

  // Which checklist item is active: uploading = item 0, then the backend step decides.
  const activeIdx =
    view.kind === 'analyzing'
      ? Math.max(1, CHECKLIST.findIndex((c) => c.steps.includes(view.step ?? '')))
      : 0;
  const isError = view.kind === 'error';
  const title =
    isError
      ? 'Something went wrong'
      : view.kind === 'uploading'
        ? `Uploading… ${Math.round(view.progress * 100)}%`
        : view.kind === 'analyzing'
          ? 'Analysing your talk'
          : view.kind === 'offline'
            ? 'Waiting for internet'
            : 'Connecting…';
  const barValue = view.kind === 'uploading' ? view.progress : view.kind === 'analyzing' ? view.progress : 0;

  return (
    <View style={styles.root}>
      <SessionHeader title="Review" step={4} onClose={onClose} />
      <Screen
        edges={['bottom']}
        footer={
          isError ? (
            <>
              {view.canRetry ? <Button title="Try again" icon="refresh" onPress={retry} /> : null}
              <Button title="Record again" variant="secondary" onPress={recordAgain} />
            </>
          ) : undefined
        }>
        {/* Breathing loader: sage-200 halo, sage-600 core, scale .88↔1.06 over 3s. */}
        <View style={styles.loaderWrap} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <Animated.View
            style={[
              styles.halo,
              { backgroundColor: isError ? theme.dangerTint : theme.successTint },
              !reducedMotion && !isError && breathe.loop,
            ]}>
            <View style={[styles.core, { backgroundColor: isError ? theme.danger : theme.success }]}>
              <MaterialIcons name={isError ? 'priority-high' : 'graphic-eq'} size={40} color={theme.onPrimary} />
            </View>
          </Animated.View>
        </View>

        <ThemedText type="title" style={styles.center} accessibilityLiveRegion="polite">
          {title}
        </ThemedText>

        {isError ? (
          <Banner tone="danger" message={view.message} />
        ) : (
          <ProgressBar value={barValue} height={8} />
        )}
        {view.kind === 'offline' ? (
          <Banner tone="warning" message="Your recording is saved and will be analysed when you reconnect." />
        ) : null}
        {view.kind === 'analyzing' && view.reconnecting ? <Banner tone="warning" message="Reconnecting to the server…" /> : null}

        {!isError ? (
          <Card>
            {CHECKLIST.map((item, i) => {
              const done = i < activeIdx;
              const active = i === activeIdx && view.kind !== 'connecting' && view.kind !== 'offline';
              return (
                <View key={item.label} style={styles.step}>
                  {done ? (
                    <View style={[styles.check, { backgroundColor: theme.success }]}>
                      <MaterialIcons name="check" size={18} color={theme.onPrimary} />
                    </View>
                  ) : active ? (
                    <View style={styles.check}>
                      <Spinner size="small" accessibilityLabel={`${item.label} in progress`} />
                    </View>
                  ) : (
                    <View style={[styles.check, styles.todo, { borderColor: theme.backgroundSelected }]} />
                  )}
                  <ThemedText type={done || active ? 'subtitle' : 'default'} themeColor={done || active ? 'text' : 'textSecondary'}>
                    {item.label}
                  </ThemedText>
                </View>
              );
            })}
          </Card>
        ) : null}

        <ThemedText themeColor="textSecondary" style={styles.center}>
          {isError
            ? `Your recording of "${topic.title}" is saved on this phone.`
            : 'This usually takes under a minute. You can leave this screen; we will pick up where we left off.'}
        </ThemedText>
        {!isError ? <Button title="Back to home" variant="secondary" onPress={onClose} style={styles.homeBtn} /> : null}
      </Screen>
    </View>
  );
}

const breathe = css.create({
  loop: {
    animationName: css.keyframes({ from: { transform: [{ scale: 0.88 }] }, to: { transform: [{ scale: 1.06 }] } }),
    animationDuration: 1500,
    animationIterationCount: 'infinite',
    animationDirection: 'alternate',
    animationTimingFunction: 'ease-in-out',
  },
});

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  loaderWrap: {
    alignItems: 'center',
    paddingTop: Spacing.four,
  },
  halo: {
    width: 140,
    height: 140,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  core: {
    width: 80,
    height: 80,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  center: {
    textAlign: 'center',
  },
  step: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three - 2,
    paddingVertical: Spacing.one + 1,
  },
  check: {
    width: 26,
    height: 26,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  todo: {
    borderWidth: 2,
  },
  homeBtn: {
    alignSelf: 'center',
    paddingHorizontal: Spacing.five,
  },
});
