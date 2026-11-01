import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { ReduceMotion, useAnimatedProps, useSharedValue, withTiming } from 'react-native-reanimated';
import Svg, { Circle } from 'react-native-svg';

import { ThemedText } from '@/components/themed-text';
import { Duration, EASE_OUT } from '@/constants/motion';
import { useTheme } from '@/hooks/use-theme';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

/** Handoff rule: ≥80 sage-600, ≥70 accent, otherwise accent-700. */
export function scoreColor(theme: ReturnType<typeof useTheme>, score: number) {
  if (score >= 80) return theme.success;
  if (score >= 70) return theme.primary;
  return theme.tintText;
}

/**
 * Overall score with an arc that fills once when the report opens. This is the app's one
 * "delight" moment (seen once per session), so it gets the longer reveal duration.
 */
export function ScoreRing({ score, size = 148, stroke = 14 }: { score: number; size?: number; stroke?: number }) {
  const theme = useTheme();
  const color = scoreColor(theme, score);
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = useSharedValue(0);

  useEffect(() => {
    progress.set(
      withTiming(Math.max(0, Math.min(100, score)) / 100, {
        duration: Duration.reveal,
        easing: EASE_OUT,
        reduceMotion: ReduceMotion.System,
      })
    );
  }, [score, progress]);

  const arcProps = useAnimatedProps(() => ({ strokeDashoffset: circumference * (1 - progress.get()) }));
  const c = size / 2;

  return (
    <View
      accessible
      accessibilityLabel={`Overall score ${Math.round(score)} out of 100`}
      style={{ width: size, height: size }}>
      <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
        <Circle cx={c} cy={c} r={radius} stroke={theme.backgroundElement} strokeWidth={stroke} fill="none" />
        <AnimatedCircle
          cx={c}
          cy={c}
          r={radius}
          stroke={color}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={`${circumference} ${circumference}`}
          animatedProps={arcProps}
          transform={`rotate(-90 ${c} ${c})`}
        />
      </Svg>
      <View style={styles.center}>
        <ThemedText type="display" style={{ fontSize: size * 0.3, lineHeight: size * 0.36 }}>
          {Math.round(score)}
        </ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          / 100
        </ThemedText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
