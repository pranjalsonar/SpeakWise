import { CameraView } from 'expo-camera';
import * as Haptics from 'expo-haptics';
import { useKeepAwake } from 'expo-keep-awake';
import { useEffect, useRef, useState } from 'react';
import { AppState, BackHandler, StyleSheet, View } from 'react-native';
import Animated, { css, useReducedMotion } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { useDialog } from '@/components/ui/dialog';
import { PressableScale } from '@/components/ui/pressable-scale';
import { ProgressBar } from '@/components/ui/progress-bar';
import { MIN_RECORDING_SEC } from '@/constants/config';
import { ENTER_POP } from '@/constants/motion';
import { Fonts, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { deleteRecording } from '@/utils/recordings';

type RecorderProps = {
  durationSec: number;
  onDone: (uri: string, seconds: number) => void;
  /** Called when the recording is discarded; `reason` is shown to the user. */
  onCancel: (reason?: string) => void;
};

type Phase = 'starting' | 'countdown' | 'recording' | 'saving';

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

export function Recorder({ durationSec, onDone, onCancel }: RecorderProps) {
  useKeepAwake();
  const theme = useTheme();
  const reducedMotion = useReducedMotion();
  const dialog = useDialog();
  const insets = useSafeAreaInsets();
  const cameraRef = useRef<CameraView>(null);
  const [phase, setPhase] = useState<Phase>('starting');
  const [count, setCount] = useState(3);
  const [elapsed, setElapsed] = useState(0);
  const startedAt = useRef(0);
  const discardReason = useRef<string | null>(null);
  const phaseRef = useRef<Phase>('starting');

  // Keep the ref in sync for event handlers (AppState / back button) that outlive renders.
  const go = (p: Phase) => {
    phaseRef.current = p;
    setPhase(p);
  };

  const stop = (reason?: string) => {
    if (reason) discardReason.current = reason;
    if (phaseRef.current === 'recording') {
      cameraRef.current?.stopRecording();
    } else if (reason) {
      onCancel(reason === 'user' ? undefined : reason);
    }
  };

  const record = async () => {
    go('recording');
    startedAt.current = Date.now();
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => undefined);
    try {
      const result = await cameraRef.current?.recordAsync({ maxDuration: durationSec });
      const seconds = (Date.now() - startedAt.current) / 1000;
      go('saving');
      if (!result?.uri) {
        onCancel(discardReason.current && discardReason.current !== 'user' ? discardReason.current : 'The recording could not be saved. Please try again.');
        return;
      }
      if (discardReason.current) {
        deleteRecording(result.uri);
        onCancel(discardReason.current === 'user' ? undefined : discardReason.current);
        return;
      }
      if (seconds < MIN_RECORDING_SEC) {
        deleteRecording(result.uri);
        onCancel('That recording was too short. Please speak for at least a few seconds.');
        return;
      }
      onDone(result.uri, seconds);
    } catch {
      onCancel('The camera could not record. Close other camera apps and try again.');
    }
  };

  // Countdown, then record.
  useEffect(() => {
    if (phase !== 'countdown') return;
    const t = setTimeout(() => (count <= 1 ? record() : setCount((c) => c - 1)), 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, count]);

  // Timer while recording.
  useEffect(() => {
    if (phase !== 'recording') return;
    const t = setInterval(() => setElapsed((Date.now() - startedAt.current) / 1000), 250);
    return () => clearInterval(t);
  }, [phase]);

  // Leaving the app or the hardware back button interrupts the recording.
  useEffect(() => {
    const appSub = AppState.addEventListener('change', (s) => {
      if (s !== 'active') stop('The recording stopped because the app was closed or interrupted. Please record again.');
    });
    const backSub = BackHandler.addEventListener('hardwareBackPress', () => {
      dialog.show({
        icon: 'videocam-off',
        tone: 'danger',
        title: 'Stop recording?',
        message: 'This recording will be discarded and you can record again.',
        actions: [
          { label: 'Discard recording', style: 'destructive', onPress: () => stop('user') },
          { label: 'Keep recording', style: 'cancel' },
        ],
      });
      return true;
    });
    return () => {
      appSub.remove();
      backSub.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const remaining = Math.max(0, durationSec - elapsed);

  return (
    <View style={styles.root}>
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        facing="front"
        mode="video"
        videoQuality="480p"
        videoBitrate={1_500_000}
        onCameraReady={() => phaseRef.current === 'starting' && go('countdown')}
        onMountError={() => onCancel('The camera could not start. Close other camera apps and try again.')}
      />

      <View style={[styles.top, { paddingTop: insets.top + Spacing.two }]}>
        {phase === 'recording' ? (
          <View style={styles.recPill}>
            <Animated.View style={[styles.recDot, { backgroundColor: theme.recording }, !reducedMotion && pulse.dot]} />
            <ThemedText type="smallBold" style={styles.light}>
              {fmt(elapsed)} / {fmt(durationSec)}
            </ThemedText>
          </View>
        ) : (
          <View />
        )}
        <PressableScale accessibilityRole="button" accessibilityLabel="Cancel recording" hitSlop={8} onPress={() => stop('user')} style={styles.cancel}>
          <ThemedText type="smallBold" style={styles.light}>
            Cancel
          </ThemedText>
        </PressableScale>
      </View>

      {phase === 'countdown' ? (
        <View style={styles.center} pointerEvents="none">
          <Animated.View key={count} entering={ENTER_POP}>
            <ThemedText style={styles.count}>{count || ''}</ThemedText>
          </Animated.View>
          <ThemedText type="subtitle" style={styles.light}>
            Get ready to speak…
          </ThemedText>
        </View>
      ) : null}
      {phase === 'starting' || phase === 'saving' ? (
        <View style={styles.center} pointerEvents="none">
          <ThemedText type="subtitle" style={styles.light}>
            {phase === 'starting' ? 'Starting camera…' : 'Saving your recording…'}
          </ThemedText>
        </View>
      ) : null}

      {phase === 'recording' ? (
        <View style={[styles.bottom, { paddingBottom: insets.bottom + Spacing.three }]}>
          <ThemedText
            accessibilityLiveRegion="polite"
            style={[styles.timer, { color: remaining <= 10 ? theme.timerFinal : '#f9f4ed' }]}>
            {fmt(Math.ceil(remaining))}
          </ThemedText>
          <ThemedText type="small" style={[styles.centerText, { color: remaining <= 10 ? theme.timerFinal : '#f9f4ed' }]}>
            {remaining <= 10 ? 'Wrap up now' : 'Look at the lens and speak clearly'}
          </ThemedText>
          <ProgressBar value={elapsed / durationSec} color={remaining <= 10 ? theme.timerFinal : theme.primary} />
          <PressableScale
            accessibilityRole="button"
            onPress={() => stop()}
            style={[styles.finish, { backgroundColor: theme.primary }]}
            pressedStyle={{ backgroundColor: theme.primaryPressed }}>
            <ThemedText style={[styles.finishLabel, { color: theme.onPrimary }]}>Finish &amp; analyse</ThemedText>
          </PressableScale>
        </View>
      ) : null}
    </View>
  );
}

// Slow opacity breathing on the red dot: state indication ("you are being recorded").
const breathe = css.keyframes({ from: { opacity: 1 }, to: { opacity: 0.35 } });
const pulse = css.create({
  dot: {
    animationName: breathe,
    animationDuration: 900,
    animationIterationCount: 'infinite',
    animationDirection: 'alternate',
    animationTimingFunction: 'ease-in-out',
  },
});

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#000',
  },
  top: {
    position: 'absolute',
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.three,
  },
  recPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    backgroundColor: 'rgba(0,0,0,0.55)',
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.one + 2,
    borderRadius: Radius.pill,
  },
  recDot: {
    width: 10,
    height: 10,
    borderRadius: Radius.pill,
  },
  cancel: {
    backgroundColor: 'rgba(0,0,0,0.55)',
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.one + 2,
    borderRadius: Radius.pill,
  },
  light: {
    color: '#ffffff',
  },
  center: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.two,
  },
  count: {
    fontFamily: Fonts.heading,
    fontSize: 160,
    lineHeight: 180,
    color: '#f9f4ed',
  },
  bottom: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 20,
    paddingTop: Spacing.four,
    gap: Spacing.two + 4,
    backgroundColor: 'rgba(31, 29, 26, 0.6)',
  },
  centerText: {
    textAlign: 'center',
  },
  timer: {
    fontFamily: Fonts.heading,
    fontSize: 64,
    lineHeight: 72,
    textAlign: 'center',
  },
  finishLabel: {
    fontFamily: Fonts.heading,
    fontSize: 17,
    lineHeight: 20,
  },
  finish: {
    minHeight: 52,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
