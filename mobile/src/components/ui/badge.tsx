import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Fonts, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type BadgeProps = {
  label: string;
  /** primary: accent-200/accent-800 · success: sage-200/sage-800 · neutral: surface/text */
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral';
};

export function Badge({ label, tone = 'primary' }: BadgeProps) {
  const theme = useTheme();
  const [bg, fg] = {
    primary: [theme.tintStrong, theme.accentText],
    success: [theme.successTint, theme.successText],
    warning: [theme.warningTint, theme.warning],
    danger: [theme.dangerTint, theme.dangerText],
    neutral: [theme.surface, theme.text],
  }[tone];

  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <ThemedText style={[styles.label, { color: fg }]}>{label}</ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.three - 2,
    paddingVertical: Spacing.one + 1,
    borderRadius: Radius.pill,
  },
  label: {
    fontFamily: Fonts.bodySemiBold,
    fontSize: 14,
    lineHeight: 18,
  },
});
