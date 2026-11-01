import type { ReactNode } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView, useSafeAreaInsets, type Edge } from 'react-native-safe-area-context';

import { Gutter, MaxContentWidth, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type ScreenProps = {
  children: ReactNode;
  /** Scrollable content (default). Set false for screens that manage their own layout. */
  scroll?: boolean;
  /** Sticky action bar pinned to the bottom (raised background, top hairline). */
  footer?: ReactNode;
  edges?: Edge[];
};

export function Screen({ children, scroll = true, footer, edges = ['top', 'bottom'] }: ScreenProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  // With a footer, the bar itself pads for the system navigation area, so its background
  // reaches the screen edge while its buttons stay clear of the gesture/nav bar.
  const footerOwnsBottom = !!footer && edges.includes('bottom');
  const safeEdges = footerOwnsBottom ? edges.filter((e) => e !== 'bottom') : edges;

  return (
    <SafeAreaView edges={safeEdges} style={[styles.root, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView behavior="padding" style={styles.root}>
        {scroll ? (
          <ScrollView
            contentContainerStyle={styles.content}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}>
            {children}
          </ScrollView>
        ) : (
          <View style={[styles.root, styles.content]}>{children}</View>
        )}
        {footer ? (
          <View
            style={[
              styles.footer,
              {
                borderTopColor: theme.border,
                backgroundColor: theme.raised,
                paddingBottom: Spacing.three + (footerOwnsBottom ? insets.bottom : 0),
              },
            ]}>
            {footer}
          </View>
        ) : null}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    width: '100%',
    maxWidth: MaxContentWidth,
    alignSelf: 'center',
    paddingHorizontal: Gutter,
    paddingTop: Spacing.three,
    paddingBottom: Spacing.five,
    gap: Gutter,
  },
  footer: {
    paddingHorizontal: Gutter,
    paddingTop: Spacing.three,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: Spacing.two,
  },
});
