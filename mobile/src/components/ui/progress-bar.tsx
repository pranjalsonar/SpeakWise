import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { ReduceMotion, useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';

import { Duration, EASE_OUT } from '@/constants/motion';
import { Radius } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type ProgressBarProps = {
  /** 0 to 1 */
  value: number;
  height?: number;
  color?: string;
  /** Glide to new values (upload/analysis progress). Turn off for values that follow a finger, like scroll. */
  animated?: boolean;
  /** Fill from empty on mount (report scores). */
  fromZero?: boolean;
};

/**
 * The fill is the only child of a fixed-size track, so animating its width re-lays-out
 * nothing else and keeps the rounded ends (scaleX would squash them).
 */
export function ProgressBar({ value, height = 8, color, animated = true, fromZero = false }: ProgressBarProps) {
  const theme = useTheme();
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const width = useSharedValue(fromZero ? 0 : pct);

  useEffect(() => {
    width.set(
      animated
        ? withTiming(pct, {
            duration: fromZero ? Duration.reveal : Duration.progress,
            easing: EASE_OUT,
            reduceMotion: ReduceMotion.System,
          })
        : pct
    );
  }, [pct, animated, fromZero, width]);

  const fillStyle = useAnimatedStyle(() => ({ width: `${width.get()}%` }));

  return (
    <View
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max: 100, now: Math.round(pct) }}
      style={[styles.track, { height, backgroundColor: theme.backgroundElement }]}>
      <Animated.View style={[styles.fill, { backgroundColor: color ?? theme.primary }, fillStyle]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    width: '100%',
    borderRadius: Radius.pill,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    borderRadius: Radius.pill,
  },
});
