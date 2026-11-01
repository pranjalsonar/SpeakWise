import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ArticleBody } from '@/components/article-body';
import { RecordingPlayer } from '@/components/report/recording-player';
import { ScoreRing, scoreColor } from '@/components/report/score-ring';
import { Bullets, Section } from '@/components/report/section';
import { ThemedText } from '@/components/themed-text';
import { Banner } from '@/components/ui/banner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useDialog } from '@/components/ui/dialog';
import { EmptyState } from '@/components/ui/empty-state';
import { IconButton } from '@/components/ui/icon-button';
import { LoadingScreen } from '@/components/ui/loading-screen';
import { ProgressBar } from '@/components/ui/progress-bar';
import { Screen } from '@/components/ui/screen';
import { useToast } from '@/components/ui/toast';
import { enterUp, STAGGER_MS } from '@/constants/motion';
import { Fonts, Gutter, Radius, Spacing } from '@/constants/theme';
import { useProfile } from '@/context/profile-context';
import { deleteSession, sessionNumber, updateSession } from '@/db/sessions';
import { getRandomTopicId } from '@/db/topics';
import { useSession } from '@/hooks/use-session';
import { useStartSession } from '@/hooks/use-start-session';
import { useTheme } from '@/hooks/use-theme';
import { deleteRecording, recordingExists } from '@/utils/recordings';
import { buildMetricCards, fmtDuration } from '@/utils/report-metrics';

// Built once at module scope (Reanimated recommends not rebuilding layout animations per render).
const HERO_ENTER = enterUp(0);
const GRID_ENTER = enterUp(STAGGER_MS * 2);

const fmtDate = (ms: number) => new Date(ms).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });

export default function ReportScreen() {
  const theme = useTheme();
  const db = useSQLiteContext();
  const router = useRouter();
  const startSession = useStartSession();
  const dialog = useDialog();
  const toast = useToast();
  const { profile } = useProfile();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { session, topic, loading } = useSession(Number(id));
  const [number, setNumber] = useState<number | null>(null);
  const [videoDeleted, setVideoDeleted] = useState(false);
  const hasVideo = !videoDeleted && recordingExists(session?.videoPath);
  const report = session?.report;
  const metrics = useMemo(() => (report ? buildMetricCards(report) : []), [report]);

  useEffect(() => {
    sessionNumber(db, Number(id)).then(setNumber);
  }, [db, id]);

  if (loading) return <LoadingScreen message="Loading your report…" />;
  if (!session || !topic || !report) {
    return (
      <Screen>
        <EmptyState icon="description" title="Report not available" message="This session has no report yet." />
        <Button title="Back to home" onPress={() => router.replace('/')} />
      </Screen>
    );
  }

  const name = report.first_name || profile?.firstName || 'there';
  const { scores, speech, context } = report;
  const headline = report.coach?.headline ?? `${report.grade} talk!`;

  const back = () => (router.canGoBack() ? router.back() : router.replace('/'));
  const newTopic = async () => {
    const next = await getRandomTopicId(db, topic.id);
    if (next) startSession(next);
  };
  const removeVideo = () =>
    dialog.show({
      icon: 'videocam-off',
      tone: 'danger',
      title: 'Delete recording?',
      message: 'Your report stays. Only the video is removed from this phone.',
      actions: [
        {
          label: 'Delete video',
          style: 'destructive',
          onPress: async () => {
            deleteRecording(session.videoPath);
            await updateSession(db, session.id, { videoPath: null });
            setVideoDeleted(true);
            toast.show('Recording deleted');
          },
        },
        { label: 'Cancel', style: 'cancel' },
      ],
    });
  const removeSession = () =>
    dialog.show({
      icon: 'delete-outline',
      tone: 'danger',
      title: 'Delete this session?',
      message: 'The report and recording will be removed from this phone. This cannot be undone.',
      actions: [
        {
          label: 'Delete session',
          style: 'destructive',
          onPress: async () => {
            deleteRecording(session.videoPath);
            await deleteSession(db, session.id);
            router.replace('/history');
            toast.show('Session deleted');
          },
        },
        { label: 'Cancel', style: 'cancel' },
      ],
    });

  return (
    <View style={[styles.root, { backgroundColor: theme.background }]}>
      <SafeAreaView edges={['top']} style={styles.topBar}>
        <IconButton icon="arrow-back" accessibilityLabel="Back" onPress={back} />
        <ThemedText type="heading">Feedback</ThemedText>
      </SafeAreaView>

      <Screen edges={['bottom']}>
        <View style={styles.intro}>
          <ThemedText type="caption">
            Session {number ?? ''} · {fmtDate(session.createdAt)}
          </ThemedText>
          <ThemedText type="title">Hey {name}, here&apos;s your report</ThemedText>
        </View>

        <Animated.View entering={HERO_ENTER}>
          <Card style={styles.hero}>
            <ScoreRing score={scores.overall} />
            <ThemedText type="heading" style={styles.centerText}>
              {headline}
            </ThemedText>
            <ThemedText themeColor="textSecondary" style={styles.centerText}>
              {topic.title} · {fmtDate(session.createdAt)} · {fmtDuration(speech.duration_sec)}
            </ThemedText>
          </Card>
        </Animated.View>

        {report.warnings.map((w) => (
          <Banner key={w} tone="warning" message={w} />
        ))}

        <Animated.View entering={GRID_ENTER} style={styles.grid}>
          {metrics.map((m) => (
            <Card key={m.key} tone="raised" style={styles.metric} accessible accessibilityLabel={`${m.label} ${Math.round(m.score)}. ${m.value ?? ''}. ${m.insight}`}>
              <View style={styles.metricHead}>
                <ThemedText type="smallBold" style={styles.flex}>
                  {m.label}
                </ThemedText>
                <ThemedText type="display" style={styles.metricScore}>
                  {Math.round(m.score)}
                </ThemedText>
              </View>
              <ProgressBar value={m.score / 100} color={scoreColor(theme, m.score)} height={7} fromZero />
              {m.value ? <ThemedText type="smallBold">{m.value}</ThemedText> : null}
              <ThemedText type="small" themeColor="textSecondary">
                {m.insight}
              </ThemedText>
            </Card>
          ))}
        </Animated.View>

        {report.coach?.strengths.length ? (
          <Card tone="sage">
            <ThemedText type="heading" style={{ color: theme.successText }}>
              What went well
            </ThemedText>
            <Bullets items={report.coach.strengths} icon="check-circle" color={theme.success} />
          </Card>
        ) : null}

        {report.coach?.improvements.length ? (
          <Card tone="peach">
            <ThemedText type="heading" style={{ color: theme.accentText }}>
              What to improve
            </ThemedText>
            {report.coach.improvements.map((i) => (
              <View key={i.area} style={styles.improvement}>
                <ThemedText type="subtitle" style={{ color: theme.accentText }}>
                  {i.area}
                </ThemedText>
                <ThemedText>{i.advice}</ThemedText>
              </View>
            ))}
          </Card>
        ) : null}

        {context.covered_points.length || context.missed_points.length ? (
          <Card tone="raised">
            <ThemedText type="heading">Content</ThemedText>
            {context.covered_points.length ? (
              <>
                <ThemedText type="smallBold">You covered</ThemedText>
                <Bullets items={context.covered_points} icon="check-circle" color={theme.success} />
              </>
            ) : null}
            {context.missed_points.length ? (
              <>
                <ThemedText type="smallBold">You could also mention</ThemedText>
                <Bullets items={context.missed_points} icon="add-circle-outline" color={theme.tintText} />
              </>
            ) : null}
            {context.note ? (
              <ThemedText type="small" themeColor="textSecondary">
                {context.note}
              </ThemedText>
            ) : null}
          </Card>
        ) : null}

        <Section icon="subject" title="Transcript" collapsible>
          <Text style={[styles.transcript, { color: theme.text }]}>
            {speech.transcript_segments.map((s, i) => (
              <Text
                key={i}
                style={
                  s.kind === 'filler'
                    ? { backgroundColor: theme.highlight, color: theme.highlightText }
                    : s.kind === 'mumble'
                      ? { backgroundColor: theme.warningTint, color: theme.text }
                      : undefined
                }>
                {s.text}{' '}
              </Text>
            ))}
          </Text>
          <ThemedText type="small" themeColor="textSecondary">
            Highlighted: filler words (peach) and unclear words (amber).
          </ThemedText>
        </Section>

        {hasVideo && session.videoPath ? (
          <Section icon="play-circle-outline" title="Your recording" collapsible>
            <RecordingPlayer uri={session.videoPath} />
            <Button title="Delete video to free space" variant="ghost" onPress={removeVideo} />
          </Section>
        ) : null}

        <Section icon="menu-book" title="Reading material" collapsible>
          <ThemedText type="heading">{topic.title}</ThemedText>
          <ArticleBody body={topic.body} fontSize={16} />
        </Section>

        <View style={styles.actions}>
          <Button title="Practice again" icon="refresh" onPress={() => startSession(topic.id)} />
          <Button title="New topic" icon="shuffle" variant="secondary" onPress={newTopic} />
          <Button title="Back to home" variant="ghost" onPress={() => router.replace('/')} />
        </View>
        <Pressable accessibilityRole="button" onPress={removeSession} hitSlop={10} style={styles.delete}>
          <ThemedText type="smallBold" themeColor="danger">
            Delete this session
          </ThemedText>
        </Pressable>
      </Screen>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three - 4,
    paddingHorizontal: Gutter,
    paddingTop: Spacing.two,
    paddingBottom: Spacing.one,
  },
  intro: {
    gap: Spacing.one,
  },
  hero: {
    alignItems: 'center',
    borderRadius: Radius.xl - 4,
    paddingVertical: Spacing.four,
    gap: Spacing.three - 4,
  },
  centerText: {
    textAlign: 'center',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.three - 4,
  },
  metric: {
    flexBasis: '47%',
    flexGrow: 1,
    borderRadius: Radius.medium + 4,
    padding: Spacing.three + 2,
    gap: Spacing.two,
  },
  metricHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.one,
  },
  metricScore: {
    fontSize: 22,
    lineHeight: 26,
  },
  flex: {
    flex: 1,
  },
  improvement: {
    gap: 2,
  },
  transcript: {
    fontFamily: Fonts.body,
    fontSize: 16,
    lineHeight: 27,
  },
  actions: {
    gap: Spacing.two + 2,
    marginTop: Spacing.two,
  },
  delete: {
    alignSelf: 'center',
    paddingVertical: Spacing.two,
  },
});
