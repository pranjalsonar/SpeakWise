import { MaterialIcons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';
import { StyleSheet, View, type PressableProps, type ViewStyle } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { PressableScale } from '@/components/ui/pressable-scale';
import { Spinner } from '@/components/ui/spinner';
import { Fonts, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type ButtonProps = Omit<PressableProps, 'style' | 'children'> & {
  title: string;
  /** primary: accent fill · secondary: outline · ghost: accent text · danger: danger outline · dangerSolid: danger fill · light: cream on accent cards */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'dangerSolid' | 'light';
  icon?: ComponentProps<typeof MaterialIcons>['name'];
  loading?: boolean;
  style?: ViewStyle;
};

/** Pill button, Caprasimo label (handoff: min-height 48, 52 for the main mobile CTA). */
export function Button({ title, variant = 'primary', icon, loading, disabled, style, ...rest }: ButtonProps) {
  const theme = useTheme();
  const isDisabled = disabled || loading;

  const palette = {
    primary: { bg: theme.primary, pressed: theme.primaryPressed, text: theme.onPrimary, border: theme.primary },
    secondary: { bg: 'transparent', pressed: theme.surface, text: theme.text, border: theme.border },
    ghost: { bg: 'transparent', pressed: theme.tint, text: theme.tintText, border: 'transparent' },
    danger: { bg: 'transparent', pressed: theme.dangerTint, text: theme.danger, border: theme.danger },
    dangerSolid: { bg: theme.danger, pressed: theme.dangerText, text: theme.onPrimary, border: theme.danger },
    light: { bg: theme.raised, pressed: theme.tint, text: theme.accentText, border: theme.raised },
  }[variant];

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled: !!isDisabled, busy: !!loading }}
      disabled={isDisabled}
      style={[
        styles.base,
        { backgroundColor: palette.bg, borderColor: palette.border, opacity: isDisabled ? 0.45 : 1 },
        style,
      ]}
      pressedStyle={{ backgroundColor: palette.pressed }}
      {...rest}>
      {loading ? (
        <Spinner size="small" color={palette.text} accessibilityLabel={`${title}, working`} />
      ) : (
        <View style={styles.content}>
          {icon ? (
            <MaterialIcons name={icon} size={20} color={palette.text} accessibilityElementsHidden importantForAccessibility="no" />
          ) : null}
          <ThemedText style={[styles.label, { color: palette.text }]}>{title}</ThemedText>
        </View>
      )}
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 52,
    paddingHorizontal: Spacing.four,
    borderRadius: Radius.pill,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
  },
  label: {
    fontFamily: Fonts.heading,
    fontSize: 17,
    lineHeight: 20,
  },
});
