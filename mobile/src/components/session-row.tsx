import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Radius, Spacing } from '@/constants/theme';
import type { HistoryItem } from '@/db/sessions';
import { useTheme } from '@/hooks/use-theme';

const fmtDate = (ms: number) => new Date(ms).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
const fmtLen = (sec: number) => (sec >= 60 ? `${Math.round(sec / 60)} min` : `${sec}s`);

/** Handoff session row: title, "Category · length · date", score circle or status badge. */
export function SessionRow({ item, onPress }: { item: HistoryItem; onPress: () => void }) {
  const theme = useTheme();
  const failed = item.stage === 'failed';
  const score = Math.round(item.overallScore ?? 0);

  return (
    <Card
      tone="raised"
      onPress={onPress}
      accessibilityLabel={`${item.topicTitle}, ${failed ? 'analysis failed' : `score ${score}`}`}
      style={styles.row}>
      <View style={styles.text}>
        <ThemedText type="subtitle" numberOfLines={2}>
          {item.topicTitle}
        </ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {item.category} · {fmtLen(item.durationSec)} · {fmtDate(item.createdAt)}
        </ThemedText>
      </View>
      {failed ? (
        <Badge label="Retry" tone="danger" />
      ) : (
        <View style={[styles.score, { backgroundColor: score >= 70 ? theme.successTint : theme.tintStrong }]}>
          <ThemedText type="display" style={[styles.scoreText, { color: score >= 70 ? theme.successText : theme.accentText }]}>
            {score}
          </ThemedText>
        </View>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three,
    borderRadius: Radius.large - 4,
  },
  text: {
    flex: 1,
    gap: Spacing.one,
  },
  score: {
    width: 52,
    height: 52,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreText: {
    fontSize: 20,
    lineHeight: 24,
  },
});
