import { StyleSheet, View } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';

import { BrandMark } from '@/components/brand-mark';
import { ThemedText } from '@/components/themed-text';
import { Spinner } from '@/components/ui/spinner';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

// Short loads finish before the loader appears, so fast screens don't flash it.
const APPEAR = FadeIn.duration(200).delay(250);

/** Calm, sparse full-screen loading state: logo mark, voice-wave spinner, optional message. */
export function LoadingScreen({ message }: { message?: string }) {
  const theme = useTheme();

  return (
    <View style={[styles.root, { backgroundColor: theme.background }]}>
      <Animated.View entering={APPEAR} style={styles.center}>
        <BrandMark size={64} />
        <Spinner size="small" accessibilityLabel={message ?? 'Loading'} />
        {message ? (
          <ThemedText type="small" themeColor="textSecondary" style={styles.message}>
            {message}
          </ThemedText>
        ) : null}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  center: {
    alignItems: 'center',
    gap: Spacing.four - 4,
  },
  message: {
    textAlign: 'center',
    maxWidth: 260,
  },
});
