import { StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { PressableScale } from '@/components/ui/pressable-scale';
import { Fonts, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type ChipProps = {
  label: string;
  selected?: boolean;
  onPress?: () => void;
};

/** 40px pill. Off: raised + transparent 2px border. On: accent-100 bg, accent border, accent-800 text. */
export function Chip({ label, selected, onPress }: ChipProps) {
  const theme = useTheme();

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ selected: !!selected }}
      onPress={onPress}
      scaleTo={0.96}
      hitSlop={{ top: 4, bottom: 4 }}
      style={[
        styles.chip,
        {
          backgroundColor: selected ? theme.tint : theme.raised,
          borderColor: selected ? theme.primary : 'transparent',
        },
      ]}
      pressedStyle={selected ? undefined : { backgroundColor: theme.surface }}>
      <ThemedText style={[styles.label, { color: selected ? theme.accentText : theme.text }]}>{label}</ThemedText>
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  chip: {
    minHeight: 40,
    paddingHorizontal: Spacing.three,
    borderRadius: Radius.pill,
    borderWidth: 2,
    justifyContent: 'center',
  },
  label: {
    fontFamily: Fonts.bodySemiBold,
    fontSize: 15,
    lineHeight: 20,
  },
});
