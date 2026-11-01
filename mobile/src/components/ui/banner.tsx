import { MaterialIcons } from '@expo/vector-icons';
import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type BannerProps = {
  message: string;
  tone?: 'info' | 'warning' | 'danger' | 'success';
};

const ICONS = {
  info: 'info-outline',
  warning: 'wifi-off',
  danger: 'error-outline',
  success: 'check-circle-outline',
} as const;

/** Handoff banner: radius 24, tinted background, dark text of the same hue. */
export function Banner({ message, tone = 'info' }: BannerProps) {
  const theme = useTheme();
  const [bg, fg] = {
    info: [theme.tint, theme.accentText],
    warning: [theme.warningTint, theme.text],
    danger: [theme.dangerTint, theme.dangerText],
    success: [theme.successTint, theme.successText],
  }[tone];

  return (
    <View accessibilityRole="alert" style={[styles.banner, { backgroundColor: bg }]}>
      <MaterialIcons name={ICONS[tone]} size={20} color={fg} />
      <ThemedText type="small" style={[styles.text, { color: fg }]}>
        {message}
      </ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two + 2,
    paddingHorizontal: Spacing.three + 2,
    paddingVertical: Spacing.three - 2,
    borderRadius: Radius.medium,
  },
  text: {
    flex: 1,
  },
});
