import { MaterialIcons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useSQLiteContext } from 'expo-sqlite';
import { useCallback, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { BrandLockup } from '@/components/brand-mark';
import { SessionRow } from '@/components/session-row';
import { ThemedText } from '@/components/themed-text';
import { Avatar, initialsOf } from '@/components/ui/avatar';
import { Banner } from '@/components/ui/banner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Screen } from '@/components/ui/screen';
import { Radius, Spacing } from '@/constants/theme';
import { useProfile } from '@/context/profile-context';
import { computeStats, getActiveSession, listHistory, type HistoryItem, type PracticeStats } from '@/db/sessions';
import { getRandomTopicId, getTopic } from '@/db/topics';
import { useOnline } from '@/hooks/use-online';
import { useStartSession } from '@/hooks/use-start-session';
import { useTheme } from '@/hooks/use-theme';
import type { Session, SessionStage } from '@/types/models';

const STAGE_LABEL: Partial<Record<SessionStage, string>> = {
  reading: 'Reading the article',
  choosing_duration: 'Choosing how long to speak',
  ready_to_record: 'Ready to record',
  recorded: 'Recorded, waiting to upload',
  uploading: 'Uploading',
  analyzing: 'Being analysed',
  failed: 'Analysis failed, tap to retry',
};

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

/** Reopen an unfinished session automatically, once per app launch. */
let resumedThisLaunch = false;

export default function HomeScreen() {
  const theme = useTheme();
  const db = useSQLiteContext();
  const router = useRouter();
  const online = useOnline();
  const startSession = useStartSession();
  const { profile } = useProfile();
  const [active, setActive] = useState<{ session: Session; title: string } | null>(null);
  const [recent, setRecent] = useState<HistoryItem[] | null>(null);
  const [stats, setStats] = useState<PracticeStats | null>(null);

  useFocusEffect(
    useCallback(() => {
      (async () => {
        const s = await getActiveSession(db);
        const title = s ? ((await getTopic(db, s.topicId))?.title ?? '') : '';
        setActive(s ? { session: s, title } : null);
        const history = await listHistory(db);
        setRecent(history.slice(0, 3));
        setStats(computeStats(history));
        if (s && !resumedThisLaunch) {
          resumedThisLaunch = true;
          router.push({ pathname: '/session/[id]', params: { id: String(s.id) } });
        }
        resumedThisLaunch = true;
      })();
    }, [db, router])
  );

  const random = async () => {
    const id = await getRandomTopicId(db);
    if (id) startSession(id);
  };

  const hasHistory = !!stats && stats.sessions > 0;

  return (
    <Screen edges={['top']}>
      <View style={styles.topBar}>
        <BrandLockup size={30} />
        <Avatar initials={initialsOf(profile?.firstName, profile?.lastName)} onPress={() => router.navigate('/profile')} />
      </View>

      <View style={styles.greeting}>
        <ThemedText type="title">
          {greeting()}, {profile?.firstName} 👋
        </ThemedText>
        <ThemedText themeColor="textSecondary">Ready for today&apos;s talk?</ThemedText>
      </View>

      {!online ? <Banner tone="warning" message="You're offline. You can read and record; analysis needs internet." /> : null}

      {active ? (
        <Card
          tone="raised"
          onPress={() => router.push({ pathname: '/session/[id]', params: { id: String(active.session.id) } })}
          style={styles.resume}>
          <View style={[styles.resumeIcon, { backgroundColor: theme.tintStrong }]}>
            <MaterialIcons name="play-arrow" size={26} color={theme.accentText} />
          </View>
          <View style={styles.flex}>
            <ThemedText type="caption">Continue your session</ThemedText>
            <ThemedText type="subtitle" numberOfLines={1}>
              {active.title}
            </ThemedText>
            <ThemedText type="small" themeColor={active.session.stage === 'failed' ? 'danger' : 'textSecondary'}>
              {STAGE_LABEL[active.session.stage]}
            </ThemedText>
          </View>
          <MaterialIcons name="chevron-right" size={26} color={theme.textSecondary} />
        </Card>
      ) : null}

      {/* Start card: accent fill with a decorative circle (handoff Home). */}
      <Card tone="accent" style={styles.start}>
        <View style={[styles.deco, { backgroundColor: theme.onPrimary }]} pointerEvents="none" />
        <ThemedText type="title" style={{ color: theme.onPrimary }}>
          Start a talk session
        </ThemedText>
        <ThemedText style={{ color: theme.onPrimary }}>
          Pick a topic, read for about 4 minutes, then speak on camera for 1 or 2 minutes.
        </ThemedText>
        <Button title="Start session" variant="light" onPress={() => router.navigate('/topics')} style={styles.startBtn} />
        <Pressable accessibilityRole="button" hitSlop={10} onPress={random} style={styles.suggest}>
          <ThemedText type="link" style={{ color: theme.onPrimary }}>
            Suggest me a topic
          </ThemedText>
        </Pressable>
      </Card>

      {hasHistory ? (
        <>
          <View style={styles.stats}>
            <StatCard value={String(stats.sessions)} label="Sessions completed" />
            <StatCard value={String(stats.minutesSpoken)} label="Minutes spoken" />
            <StatCard value={`${stats.streakDays} ${stats.streakDays === 1 ? 'day' : 'days'}`} label="Current streak" sage />
          </View>

          <View style={styles.sectionHead}>
            <ThemedText type="heading">Recent sessions</ThemedText>
            <Pressable accessibilityRole="button" hitSlop={10} onPress={() => router.navigate('/history')}>
              <ThemedText type="link">See all</ThemedText>
            </Pressable>
          </View>
          {recent?.map((item) => (
            <SessionRow
              key={item.id}
              item={item}
              onPress={() =>
                router.push(
                  item.stage === 'failed'
                    ? { pathname: '/session/[id]', params: { id: String(item.id) } }
                    : { pathname: '/report/[id]', params: { id: String(item.id) } }
                )
              }
            />
          ))}
        </>
      ) : recent ? (
        <View style={[styles.empty, { borderColor: theme.backgroundSelected }]}>
          <View style={[styles.emptyIcon, { backgroundColor: theme.tintStrong }]}>
            <MaterialIcons name="mic" size={28} color={theme.accentText} />
          </View>
          <ThemedText type="heading">No sessions yet</ThemedText>
          <ThemedText themeColor="textSecondary" style={styles.centerText}>
            Your first talk takes about 10 minutes: 4 to read, 1 or 2 to speak, and a minute for your feedback.
          </ThemedText>
        </View>
      ) : null}
    </Screen>
  );
}

function StatCard({ value, label, sage }: { value: string; label: string; sage?: boolean }) {
  return (
    <Card tone={sage ? 'sage' : 'surface'} style={styles.stat}>
      <ThemedText type="display" style={styles.statValue} numberOfLines={1} adjustsFontSizeToFit>
        {value}
      </ThemedText>
      <ThemedText type="small" themeColor="textSecondary">
        {label}
      </ThemedText>
    </Card>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Spacing.two,
  },
  greeting: {
    gap: Spacing.one,
  },
  resume: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three - 4,
    borderRadius: Radius.large - 4,
  },
  resumeIcon: {
    width: 48,
    height: 48,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  flex: {
    flex: 1,
    gap: 2,
  },
  start: {
    borderRadius: Radius.xl - 4,
    padding: Spacing.four,
    gap: Spacing.three - 4,
  },
  deco: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: Radius.pill,
    top: -50,
    right: -60,
    opacity: 0.1,
  },
  startBtn: {
    marginTop: Spacing.two,
  },
  suggest: {
    alignSelf: 'center',
    paddingVertical: Spacing.one,
  },
  stats: {
    flexDirection: 'row',
    gap: Spacing.two + 2,
  },
  stat: {
    flex: 1,
    borderRadius: Radius.medium + 4,
    padding: Spacing.three,
    gap: Spacing.one,
  },
  statValue: {
    fontSize: 24,
    lineHeight: 28,
  },
  sectionHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  empty: {
    alignItems: 'center',
    gap: Spacing.two,
    padding: Spacing.four,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderRadius: Radius.large,
  },
  emptyIcon: {
    width: 56,
    height: 56,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.one,
  },
  centerText: {
    textAlign: 'center',
  },
});
