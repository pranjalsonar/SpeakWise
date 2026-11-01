import { StyleSheet, Text, type TextProps } from 'react-native';

import { Fonts, ThemeColor } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export type ThemedTextProps = TextProps & {
  type?:
    | 'default'
    | 'title'
    | 'heading'
    | 'subtitle'
    | 'small'
    | 'smallBold'
    | 'caption'
    | 'link'
    | 'display'
    | 'code';
  themeColor?: ThemeColor;
};

export function ThemedText({ style, type = 'default', themeColor, ...rest }: ThemedTextProps) {
  const theme = useTheme();
  const fallback = type === 'link' || type === 'caption' ? theme.tintText : theme.text;
  const color = themeColor ? theme[themeColor] : fallback;

  return <Text style={[{ color }, styles[type], style]} {...rest} />;
}

// Custom fonts on Android need the weight-specific family, so no fontWeight here.
const styles = StyleSheet.create({
  default: {
    fontFamily: Fonts.body,
    fontSize: 16,
    lineHeight: 24,
  },
  /** Caprasimo H1 (mobile 26–30). */
  title: {
    fontFamily: Fonts.heading,
    fontSize: 28,
    lineHeight: 33,
    letterSpacing: -0.3,
  },
  heading: {
    fontFamily: Fonts.heading,
    fontSize: 21,
    lineHeight: 26,
  },
  subtitle: {
    fontFamily: Fonts.bodyBold,
    fontSize: 17,
    lineHeight: 23,
  },
  small: {
    fontFamily: Fonts.body,
    fontSize: 14,
    lineHeight: 20,
  },
  smallBold: {
    fontFamily: Fonts.bodyBold,
    fontSize: 14,
    lineHeight: 20,
  },
  /** Overline: 12, uppercase, tracked, accent-700. */
  caption: {
    fontFamily: Fonts.bodyBold,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  link: {
    fontFamily: Fonts.bodyBold,
    fontSize: 15,
    lineHeight: 22,
    textDecorationLine: 'underline',
  },
  /** Numbers and short emphasis in Caprasimo (scores, stats). */
  display: {
    fontFamily: Fonts.heading,
    fontSize: 26,
    lineHeight: 30,
  },
  code: {
    fontFamily: Fonts.mono,
    fontSize: 12,
  },
});
