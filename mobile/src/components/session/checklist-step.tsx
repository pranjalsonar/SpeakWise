import { MaterialIcons } from '@expo/vector-icons';
import { useCameraPermissions, useMicrophonePermissions, type PermissionResponse } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useState } from 'react';
import { AppState, Linking, StyleSheet, View } from 'react-native';

import { Recorder } from '@/components/session/recorder';
import { SessionHeader } from '@/components/session/session-header';
import type { StepProps } from '@/components/session/types';
import { ThemedText } from '@/components/themed-text';
import { Banner } from '@/components/ui/banner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useDialog } from '@/components/ui/dialog';
import { Screen } from '@/components/ui/screen';
import { Spinner } from '@/components/ui/spinner';
import { MAX_UPLOAD_SEC, MIN_FREE_BYTES, MIN_RECORDING_SEC } from '@/constants/config';
import { Radius, Spacing } from '@/constants/theme';
import { useOnline } from '@/hooks/use-online';
import { useTheme } from '@/hooks/use-theme';
import { checkHealth, resolveBackend } from '@/services/api';
import { freeSpaceBytes, keepRecording } from '@/utils/recordings';

type CheckState = 'ok' | 'warn' | 'bad' | 'loading';

const TIPS = [
  'Sit facing a window or lamp so your face is well lit.',
  'Hold the phone at eye level with your head and shoulders in the frame.',
  'Look at the camera lens, not at your own picture.',
  'Find a quiet place and speak a little louder than usual.',
];

export function ChecklistStep({ session, topic, update, onClose }: StepProps) {
  const theme = useTheme();
  const db = useSQLiteContext();
  const online = useOnline();
  const dialog = useDialog();
  const [camera, requestCamera, getCamera] = useCameraPermissions();
  const [mic, requestMic, getMic] = useMicrophonePermissions();
  const [server, setServer] = useState<CheckState>('loading');
  const [recording, setRecording] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const free = freeSpaceBytes();
  const storageOk = free == null || free >= MIN_FREE_BYTES;

  const checkServer = () => {
    setServer('loading');
    resolveBackend(db)
      .then(checkHealth)
      .then(() => setServer('ok'))
      .catch(() => setServer('warn'));
  };

  useEffect(() => {
    let cancelled = false;
    resolveBackend(db)
      .then(checkHealth)
      .then(() => !cancelled && setServer('ok'))
      .catch(() => !cancelled && setServer('warn'));
    return () => {
      cancelled = true;
    };
  }, [db, online]);

  // Permissions may change in system Settings while the app is in the background.
  useEffect(() => {
    const sub = AppState.addEventListener('change', (s) => {
      if (s === 'active') {
        getCamera();
        getMic();
      }
    });
    return () => sub.remove();
  }, [getCamera, getMic]);

  const askPermission = async (current: PermissionResponse | null, request: () => Promise<PermissionResponse>) => {
    if (current && !current.granted && !current.canAskAgain) {
      dialog.show({
        icon: 'lock-outline',
        title: 'Permission needed',
        message: 'This permission was turned off. Allow it for SpeakWise in your phone settings, then come back.',
        actions: [
          { label: 'Open settings', onPress: () => Linking.openSettings() },
          { label: 'Not now', style: 'cancel' },
        ],
      });
      return;
    }
    await request();
  };

  const saveVideo = async (tempUri: string) => {
    setSaving(true);
    try {
      const videoPath = await keepRecording(tempUri, session.id);
      await update({ videoPath, stage: 'recorded', jobId: null, error: null });
    } catch {
      setNotice('Could not save the recording. Please free some storage and try again.');
      setSaving(false);
    }
  };

  const pickVideo = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['videos'], allowsEditing: false, quality: 1 });
    if (res.canceled || !res.assets?.length) return;
    const asset = res.assets[0];
    const seconds = (asset.duration ?? 0) / 1000;
    if (seconds > MAX_UPLOAD_SEC) {
      setNotice('That video is longer than 2 minutes. Please choose a shorter one.');
      return;
    }
    if (seconds && seconds < MIN_RECORDING_SEC) {
      setNotice('That video is too short to analyse.');
      return;
    }
    await saveVideo(asset.uri);
  };

  if (recording && session.durationSec) {
    return (
      <Recorder
        durationSec={session.durationSec}
        onDone={(uri) => {
          setRecording(false);
          saveVideo(uri);
        }}
        onCancel={(reason) => {
          setRecording(false);
          setNotice(reason ?? null);
        }}
      />
    );
  }

  const cameraState: CheckState = camera?.granted ? 'ok' : 'bad';
  const micState: CheckState = mic?.granted ? 'ok' : 'bad';
  const canRecord = !!camera?.granted && !!mic?.granted && storageOk && !saving;

  return (
    <View style={styles.root}>
    <SessionHeader title="Record" step={3} onClose={onClose} />
    <Screen
      edges={['bottom']}
      footer={
        <>
          <Button title={saving ? 'Saving…' : 'Start recording'} icon="videocam" onPress={() => { setNotice(null); setRecording(true); }} disabled={!canRecord} loading={saving} />
          <View style={styles.footerRow}>
            <Button title="Upload video" variant="secondary" onPress={pickVideo} disabled={saving} style={styles.flex} />
            <Button title={`${(session.durationSec ?? 60) / 60} min`} icon="timer" variant="secondary" onPress={() => update({ stage: 'choosing_duration' })} disabled={saving} style={styles.flex} />
          </View>
        </>
      }>
      <View style={styles.header}>
        <ThemedText type="title">Get ready</ThemedText>
        <ThemedText themeColor="textSecondary">
          You&apos;ll speak about <ThemedText type="smallBold">{topic.title}</ThemedText> for{' '}
          {(session.durationSec ?? 60) / 60} minute{session.durationSec === 120 ? 's' : ''}.
        </ThemedText>
      </View>

      {notice ? <Banner tone="warning" message={notice} /> : null}
      {!online ? <Banner tone="warning" message="You're offline. You can still record; we'll analyse it when you're back online." /> : null}

      <Card tone="raised">
        <CheckRow
          state={cameraState}
          title="Camera"
          detail={camera?.granted ? 'Allowed' : 'Needed to see your eye contact and posture'}
          action={!camera?.granted ? <Button title="Allow" variant="secondary" onPress={() => askPermission(camera, requestCamera)} style={styles.smallBtn} /> : null}
        />
        <CheckRow
          state={micState}
          title="Microphone"
          detail={mic?.granted ? 'Allowed' : 'Needed to hear your speech'}
          action={!mic?.granted ? <Button title="Allow" variant="secondary" onPress={() => askPermission(mic, requestMic)} style={styles.smallBtn} /> : null}
          divider
        />
        <CheckRow
          state={server}
          title="SpeakWise server"
          detail={server === 'ok' ? 'Connected' : server === 'loading' ? 'Checking…' : 'Not reachable yet. You can record now and analyse later.'}
          action={server === 'warn' ? <Button title="Retry" variant="ghost" onPress={checkServer} style={styles.smallBtn} /> : null}
          divider
        />
        <CheckRow
          state={storageOk ? 'ok' : 'bad'}
          title="Storage"
          detail={storageOk ? 'Enough space' : 'Less than 200 MB free. Delete some files or old recordings.'}
          divider
        />
      </Card>

      <ThemedText type="caption">Tips for a great recording</ThemedText>
      <Card tone="raised">
        {TIPS.map((t) => (
          <View key={t} style={styles.tip}>
            <MaterialIcons name="lightbulb-outline" size={18} color={theme.tintText} style={styles.tipIcon} />
            <ThemedText type="small" style={styles.tipText}>
              {t}
            </ThemedText>
          </View>
        ))}
      </Card>
    </Screen>
    </View>
  );
}

function CheckRow({
  state,
  title,
  detail,
  action,
  divider,
}: {
  state: CheckState;
  title: string;
  detail: string;
  action?: React.ReactNode;
  divider?: boolean;
}) {
  const theme = useTheme();
  const icon = { ok: 'check-circle', warn: 'error-outline', bad: 'cancel', loading: 'hourglass-empty' } as const;
  const color = { ok: theme.success, warn: theme.warning, bad: theme.danger, loading: theme.primary }[state];

  return (
    <View style={[styles.row, divider && { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: theme.border }]}>
      {state === 'loading' ? (
        <View style={styles.rowIcon}>
          <Spinner size="small" accessibilityLabel={`Checking ${title}`} />
        </View>
      ) : (
        <MaterialIcons name={icon[state]} size={24} color={color} style={styles.rowIcon} />
      )}
      <View style={styles.rowText}>
        <ThemedText type="subtitle">{title}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {detail}
        </ThemedText>
      </View>
      {action}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  header: {
    gap: Spacing.two,
  },
  footerRow: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  flex: {
    flex: 1,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three - 4,
    paddingVertical: Spacing.two + 4,
  },
  rowIcon: {
    width: 24,
  },
  rowText: {
    flex: 1,
    gap: 2,
  },
  smallBtn: {
    minHeight: 38,
    paddingHorizontal: Spacing.three,
    borderRadius: Radius.small,
  },
  tip: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  tipIcon: {
    marginTop: 1,
  },
  tipText: {
    flex: 1,
  },
});
