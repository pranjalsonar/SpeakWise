import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { IconButton } from '@/components/ui/icon-button';
import { ProgressBar } from '@/components/ui/progress-bar';
import { Gutter, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

const TOTAL_STEPS = 4;

type SessionHeaderProps = {
  title: string;
  step: 1 | 2 | 3 | 4;
  onClose: () => void;
  /** Extra controls on the right, e.g. the reader's A−/A+. */
  right?: ReactNode;
  /** When set (0–1), a thin reading-progress bar replaces the step segments. */
  progress?: number;
};

/** Focus layout top bar: × · step name · "Step n of 4" · optional controls, then the progress. */
export function SessionHeader({ title, step, onClose, right, progress }: SessionHeaderProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.wrap, { paddingTop: insets.top + Spacing.two, backgroundColor: theme.background }]}>
      <View style={styles.row}>
        <IconButton icon="close" accessibilityLabel="Close session" onPress={onClose} />
        <View style={styles.titles}>
          <ThemedText type="heading" numberOfLines={1}>
            {title}
          </ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            Step {step} of {TOTAL_STEPS}
          </ThemedText>
        </View>
        {right ? <View style={styles.right}>{right}</View> : null}
      </View>

      {progress == null ? (
        <View style={styles.segments} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          {Array.from({ length: TOTAL_STEPS }, (_, i) => (
            <View
              key={i}
              style={[styles.segment, { backgroundColor: i < step ? theme.primary : theme.backgroundElement }]}
            />
          ))}
        </View>
      ) : (
        <View style={styles.readBar}>
          <ProgressBar value={progress} height={4} animated={false} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingBottom: Spacing.two,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three - 4,
    paddingHorizontal: Gutter,
    paddingBottom: Spacing.three - 4,
  },
  titles: {
    flex: 1,
  },
  right: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  segments: {
    flexDirection: 'row',
    gap: Spacing.two,
    paddingHorizontal: Gutter,
  },
  segment: {
    flex: 1,
    height: 5,
    borderRadius: Radius.pill,
  },
  readBar: {
    paddingHorizontal: Gutter,
  },
});
