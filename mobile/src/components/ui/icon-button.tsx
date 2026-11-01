import { MaterialIcons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';
import { StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { PressableScale } from '@/components/ui/pressable-scale';
import { Fonts, Radius } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type IconButtonProps = {
  accessibilityLabel: string;
  onPress: () => void;
  icon?: ComponentProps<typeof MaterialIcons>['name'];
  /** Text instead of an icon, e.g. "A−". */
  label?: string;
  /** outline: transparent + divider ring (×, back) · filled: surface circle (A−/A+) */
  variant?: 'outline' | 'filled';
  disabled?: boolean;
};

/** 44px circle button used in the focus/top bars. */
export function IconButton({ accessibilityLabel, onPress, icon, label, variant = 'outline', disabled }: IconButtonProps) {
  const theme = useTheme();

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      disabled={disabled}
      hitSlop={4}
      scaleTo={0.94}
      style={[
        styles.circle,
        variant === 'outline'
          ? { borderColor: theme.border, backgroundColor: 'transparent' }
          : { borderColor: theme.surface, backgroundColor: theme.surface },
        disabled ? styles.disabled : null,
      ]}
      pressedStyle={{ backgroundColor: theme.surface }}>
      {icon ? <MaterialIcons name={icon} size={24} color={theme.text} /> : null}
      {label ? <ThemedText style={styles.label}>{label}</ThemedText> : null}
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  circle: {
    width: 44,
    height: 44,
    borderRadius: Radius.pill,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontFamily: Fonts.bodyBold,
    fontSize: 16,
    lineHeight: 20,
  },
  disabled: {
    opacity: 0.4,
  },
});
