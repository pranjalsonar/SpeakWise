import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { PressableScale } from '@/components/ui/pressable-scale';
import { Fonts, Radius } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export function initialsOf(firstName?: string | null, lastName?: string | null) {
  return [firstName, lastName]
    .filter((n): n is string => !!n)
    .map((n) => n[0].toUpperCase())
    .join('');
}

/** Initials on sage-300 (handoff avatar). */
export function Avatar({ initials, size = 44, onPress }: { initials: string; size?: number; onPress?: () => void }) {
  const theme = useTheme();
  const circle = [styles.circle, { width: size, height: size, backgroundColor: theme.avatar }];
  const label = (
    <ThemedText style={[styles.text, { fontSize: size * 0.36, lineHeight: size * 0.44, color: theme.successText }]}>
      {initials}
    </ThemedText>
  );

  if (onPress) {
    return (
      <PressableScale accessibilityRole="button" accessibilityLabel="Open profile" onPress={onPress} hitSlop={4} scaleTo={0.94} style={circle}>
        {label}
      </PressableScale>
    );
  }
  return <View style={circle}>{label}</View>;
}

const styles = StyleSheet.create({
  circle: {
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontFamily: Fonts.bodyBold,
  },
});
