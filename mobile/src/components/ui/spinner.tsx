import { StyleSheet, View } from 'react-native';
import Animated, { css, useReducedMotion } from 'react-native-reanimated';

import { Radius } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type SpinnerProps = {
  /** small: inline (buttons, rows) · large: full-screen loading */
  size?: 'small' | 'large';
  color?: string;
  accessibilityLabel?: string;
};

const BARS = 4;
/** Resting heights are the logo's sound-wave bars (110/230/305/175), so the still state is the mark. */
const REST = [0.36, 0.75, 1, 0.57];

/**
 * SpeakWise loader: the logo's four sound-wave bars rising and falling like a voice meter.
 * Only `transform: scaleY` animates (UI thread, no layout); each bar is offset by 120ms.
 */
export function Spinner({ size = 'small', color, accessibilityLabel = 'Loading' }: SpinnerProps) {
  const theme = useTheme();
  const reducedMotion = useReducedMotion();
  // Small fits a 24px icon slot (4×3.5 + 3×3 = 23px wide).
  const dims = size === 'large' ? { bar: 8, gap: 7, height: 40 } : { bar: 3.5, gap: 3, height: 18 };

  return (
    <View
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={accessibilityLabel}
      style={[styles.row, { gap: dims.gap, height: dims.height }]}>
      {Array.from({ length: BARS }, (_, i) => (
        <Animated.View
          key={i}
          style={[
            styles.bar,
            {
              width: dims.bar,
              height: dims.height,
              backgroundColor: color ?? theme.primary,
              transform: [{ scaleY: REST[i] }],
            },
            !reducedMotion && wave.bar,
            !reducedMotion && { animationDelay: i * 120 },
          ]}
        />
      ))}
    </View>
  );
}

const wave = css.create({
  bar: {
    animationName: css.keyframes({
      '0%': { transform: [{ scaleY: 0.3 }] },
      '50%': { transform: [{ scaleY: 1 }] },
      '100%': { transform: [{ scaleY: 0.3 }] },
    }),
    animationDuration: 900,
    animationIterationCount: 'infinite',
    animationTimingFunction: 'ease-in-out',
  },
});

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  bar: {
    borderRadius: Radius.pill,
  },
});
