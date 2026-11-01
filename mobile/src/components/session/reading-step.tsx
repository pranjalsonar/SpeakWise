import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useRef, useState, type ComponentRef } from 'react';
import { ScrollView, StyleSheet, View, type NativeScrollEvent, type NativeSyntheticEvent } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ArticleBody } from '@/components/article-body';
import { SessionHeader } from '@/components/session/session-header';
import type { StepProps } from '@/components/session/types';
import { ThemedText } from '@/components/themed-text';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useDialog } from '@/components/ui/dialog';
import { IconButton } from '@/components/ui/icon-button';
import { READER_FONT_KEY } from '@/constants/config';
import { Fonts, Gutter, MaxContentWidth, Radius, Spacing } from '@/constants/theme';
import { getSetting, setSetting } from '@/db/settings';
import { useTheme } from '@/hooks/use-theme';

/** Literata 18px base; A−/A+ step by 2px (−2…+4). */
const FONT_SIZES = [16, 18, 20, 22];
const DEFAULT_FONT_IDX = 1;
const READ_ENOUGH = 0.9;

export function ReadingStep({ session, topic, update, onClose }: StepProps) {
  const theme = useTheme();
  const db = useSQLiteContext();
  const insets = useSafeAreaInsets();
  const dialog = useDialog();
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  const [progress, setProgress] = useState(session.readingProgress);
  const [fontIdx, setFontIdx] = useState(DEFAULT_FONT_IDX);
  const lastSaved = useRef(session.readingProgress);
  const restored = useRef(session.readingProgress <= 0);
  const viewport = useRef(0);

  useEffect(() => {
    getSetting(db, READER_FONT_KEY).then((v) => {
      const idx = v ? FONT_SIZES.indexOf(Number(v)) : -1;
      if (idx >= 0) setFontIdx(idx);
    });
  }, [db]);

  // Save reading position every few percent so the reader reopens where the user left off.
  useEffect(() => {
    if (Math.abs(progress - lastSaved.current) < 0.03 && progress < 0.99) return;
    const t = setTimeout(() => {
      lastSaved.current = progress;
      update({ readingProgress: progress });
    }, 800);
    return () => clearTimeout(t);
  }, [progress, update]);

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
    const max = Math.max(1, contentSize.height - layoutMeasurement.height);
    setProgress(Math.min(1, Math.max(0, contentOffset.y / max)));
  };

  const onContentSize = (_w: number, h: number) => {
    if (restored.current || !viewport.current) return;
    restored.current = true;
    scrollRef.current?.scrollTo({ y: session.readingProgress * Math.max(0, h - viewport.current), animated: false });
  };

  const changeFont = (delta: number) => {
    const next = Math.max(0, Math.min(FONT_SIZES.length - 1, fontIdx + delta));
    setFontIdx(next);
    setSetting(db, READER_FONT_KEY, String(FONT_SIZES[next]));
  };

  const ready = () => {
    const go = () => update({ stage: 'choosing_duration', readingProgress: progress });
    if (progress >= READ_ENOUGH) return go();
    dialog.show({
      icon: 'menu-book',
      title: `You've read ${Math.round(progress * 100)}%`,
      message: 'Reading the whole article gives you more to talk about. Start anyway?',
      actions: [
        { label: 'Start anyway', onPress: go },
        { label: 'Keep reading', style: 'cancel' },
      ],
    });
  };

  const pct = Math.round(progress * 100);

  return (
    <View style={styles.root}>
      <SessionHeader
        title="Prepare"
        step={1}
        onClose={onClose}
        progress={progress}
        right={
          <>
            <IconButton variant="filled" label="A−" accessibilityLabel="Smaller text" onPress={() => changeFont(-1)} disabled={fontIdx === 0} />
            <IconButton
              variant="filled"
              label="A+"
              accessibilityLabel="Larger text"
              onPress={() => changeFont(1)}
              disabled={fontIdx === FONT_SIZES.length - 1}
            />
          </>
        }
      />

      <ScrollView
        ref={scrollRef}
        onLayout={(e) => (viewport.current = e.nativeEvent.layout.height)}
        onContentSizeChange={onContentSize}
        onScroll={onScroll}
        scrollEventThrottle={100}
        contentContainerStyle={styles.content}>
        <View style={styles.badges}>
          <Badge label={topic.category} tone="neutral" />
          <Badge label={topic.level === 'Easy' ? 'Beginner' : topic.level} tone="success" />
        </View>
        <ThemedText type="title" accessibilityRole="header">
          {topic.title}
        </ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          ≈ {topic.readMinutes} min read · {topic.wordCount} words
        </ThemedText>

        <ArticleBody body={topic.body} fontSize={FONT_SIZES[fontIdx]} />

        <Card tone="sage" style={styles.keyPoints}>
          <ThemedText type="heading" style={{ color: theme.successText }}>
            Key points to cover
          </ThemedText>
          {topic.talkingPoints.map((p, i) => (
            <View key={p} style={styles.point}>
              <ThemedText style={[styles.pointNum, { color: theme.successText }]}>{i + 1}.</ThemedText>
              <ThemedText style={[styles.pointText, { color: theme.successText }]}>{p}</ThemedText>
            </View>
          ))}
        </Card>
      </ScrollView>

      <View
        style={[
          styles.footer,
          { borderTopColor: theme.border, backgroundColor: theme.raised, paddingBottom: Spacing.three + insets.bottom },
        ]}>
        <ThemedText type="smallBold">{pct}% read</ThemedText>
        <Button title="I'm ready, start talk" onPress={ready} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  content: {
    paddingHorizontal: Gutter,
    paddingTop: Spacing.four - 4,
    paddingBottom: Spacing.five,
    gap: Spacing.three,
    width: '100%',
    maxWidth: MaxContentWidth,
    alignSelf: 'center',
  },
  badges: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  keyPoints: {
    marginTop: Spacing.three,
    borderRadius: Radius.large - 4,
  },
  point: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  pointNum: {
    fontFamily: Fonts.bodyBold,
    width: 20,
  },
  pointText: {
    flex: 1,
  },
  footer: {
    paddingHorizontal: Gutter,
    paddingTop: Spacing.three - 4,
    gap: Spacing.three - 4,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});
