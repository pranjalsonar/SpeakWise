import { useState, type ReactNode } from 'react';
import { Pressable, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';
import Animated, { css } from 'react-native-reanimated';

import { Duration, EASE_OUT_CSS } from '@/constants/motion';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

type PressableScaleProps = Omit<PressableProps, 'style' | 'children'> & {
  children?: ReactNode;
  style?: StyleProp<ViewStyle>;
  /** Extra style while pressed, e.g. a darker background. */
  pressedStyle?: StyleProp<ViewStyle>;
  /** 0.97 for buttons; larger surfaces use a smaller change (0.98). */
  scaleTo?: number;
};

/**
 * Press feedback for every tappable surface: scale on press-in over 120ms with a strong
 * ease-out. It's a Reanimated CSS transition, so it runs on the UI thread, retargets if the
 * finger lifts mid-way, and needs no shared values.
 */
export function PressableScale({
  children,
  style,
  pressedStyle,
  scaleTo = 0.97,
  disabled,
  onPressIn,
  onPressOut,
  ...rest
}: PressableScaleProps) {
  const [pressed, setPressed] = useState(false);
  const active = pressed && !disabled;

  return (
    <AnimatedPressable
      disabled={disabled}
      pressRetentionOffset={16}
      onPressIn={(e) => {
        setPressed(true);
        onPressIn?.(e);
      }}
      onPressOut={(e) => {
        setPressed(false);
        onPressOut?.(e);
      }}
      style={[styles.base, style, active && pressedStyle, { transform: [{ scale: active ? scaleTo : 1 }] }]}
      {...rest}>
      {children}
    </AnimatedPressable>
  );
}

const styles = css.create({
  base: {
    transitionProperty: ['transform', 'backgroundColor', 'borderColor'],
    transitionDuration: Duration.press,
    transitionTimingFunction: EASE_OUT_CSS,
  },
});
