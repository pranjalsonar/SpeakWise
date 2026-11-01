import { MaterialIcons } from '@expo/vector-icons';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { Fonts, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type SearchBarProps = {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
};

export function SearchBar({ value, onChangeText, placeholder = 'Search' }: SearchBarProps) {
  const theme = useTheme();

  return (
    <View style={[styles.bar, { backgroundColor: theme.raised, borderColor: theme.border }]}>
      <MaterialIcons name="search" size={22} color={theme.textSecondary} />
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={theme.textSecondary}
        selectionColor={theme.primary}
        returnKeyType="search"
        autoCorrect={false}
        style={[styles.input, { color: theme.text }]}
      />
      {value ? (
        <Pressable accessibilityLabel="Clear search" hitSlop={12} onPress={() => onChangeText('')}>
          <MaterialIcons name="close" size={20} color={theme.textSecondary} />
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    minHeight: 52,
    paddingHorizontal: Spacing.three + 2,
    borderWidth: 1.5,
    borderRadius: Radius.pill,
  },
  input: {
    flex: 1,
    fontFamily: Fonts.body,
    fontSize: 16,
    paddingVertical: Spacing.two,
  },
});
