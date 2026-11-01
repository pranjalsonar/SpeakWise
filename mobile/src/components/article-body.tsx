import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Fonts, Spacing } from '@/constants/theme';

/**
 * Renders the small markdown subset used by the articles: "## " headings and paragraphs.
 * Reading text is Literata, line-height 1.7 (handoff); headings are Caprasimo.
 */
export function ArticleBody({ body, fontSize = 18 }: { body: string; fontSize?: number }) {
  const blocks = body
    .split(/\n{2,}/)
    .map((b) => b.trim())
    .filter(Boolean);
  const lineHeight = Math.round(fontSize * 1.7);

  return (
    <View style={styles.body}>
      {blocks.map((block, i) =>
        block.startsWith('#') ? (
          <ThemedText
            key={i}
            accessibilityRole="header"
            type="heading"
            style={[styles.heading, { fontSize: fontSize + 4, lineHeight: Math.round((fontSize + 4) * 1.2) }]}>
            {block.replace(/^#+\s*/, '')}
          </ThemedText>
        ) : (
          <ThemedText key={i} style={{ fontFamily: Fonts.reading, fontSize, lineHeight }}>
            {block.replace(/\n/g, ' ')}
          </ThemedText>
        )
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  body: {
    gap: Spacing.three,
  },
  heading: {
    marginTop: Spacing.three,
  },
});
