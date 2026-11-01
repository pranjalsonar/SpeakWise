import { StyleSheet, TextInput, View, type TextInputProps } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Fonts, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type TextFieldProps = TextInputProps & {
  label: string;
  optional?: boolean;
  error?: string;
};

/** Pill input on the raised neutral, divider border; error border #B3402C with text below. */
export function TextField({ label, optional, error, style, ...rest }: TextFieldProps) {
  const theme = useTheme();

  return (
    <View style={styles.field}>
      <ThemedText type="smallBold">
        {label}
        {optional && <ThemedText type="small" themeColor="textSecondary"> (optional)</ThemedText>}
      </ThemedText>
      <TextInput
        placeholderTextColor={theme.textSecondary}
        selectionColor={theme.primary}
        style={[
          styles.input,
          {
            color: theme.text,
            backgroundColor: theme.raised,
            borderColor: error ? theme.danger : theme.border,
          },
          style,
        ]}
        {...rest}
      />
      {error ? (
        <ThemedText type="small" themeColor="danger">
          {error}
        </ThemedText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    gap: Spacing.one + 2,
  },
  input: {
    minHeight: 52,
    borderWidth: 1.5,
    borderRadius: Radius.pill,
    paddingHorizontal: Spacing.four - 4,
    fontFamily: Fonts.body,
    fontSize: 16,
  },
});
