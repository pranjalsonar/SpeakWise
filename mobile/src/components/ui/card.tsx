import { StyleSheet, View, type ViewProps, type ViewStyle } from 'react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export type CardTone = 'surface' | 'raised' | 'accent' | 'peach' | 'sage';

type CardProps = ViewProps & {
  onPress?: () => void;
  /** surface (default card) · raised (list rows, metric cards) · accent (start card) · peach · sage */
  tone?: CardTone;
  /** @deprecated use tone="peach" */
  tinted?: boolean;
  style?: ViewStyle | ViewStyle[];
};

/** Flat, soft card (handoff radius 32, no border, no shadow). */
export function Card({ onPress, tone, tinted, style, children, ...rest }: CardProps) {
  const theme = useTheme();
  const resolved: CardTone = tone ?? (tinted ? 'peach' : 'surface');
  const bg = {
    surface: theme.surface,
    raised: theme.raised,
    accent: theme.primary,
    peach: theme.tintStrong,
    sage: theme.successTint,
  }[resolved];
  const base = [styles.card, { backgroundColor: bg }];

  if (onPress) {
    return (
      <PressableScale accessibilityRole="button" onPress={onPress} scaleTo={0.98} style={[base, style]} {...rest}>
        {children}
      </PressableScale>
    );
  }
  return (
    <View style={[base, style]} {...rest}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: Radius.large,
    padding: Spacing.four - 4,
    gap: Spacing.two + 2,
    overflow: 'hidden',
  },
});
