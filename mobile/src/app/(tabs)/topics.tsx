import { MaterialIcons } from '@expo/vector-icons';
import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Card } from '@/components/ui/card';
import { Chip } from '@/components/ui/chip';
import { EmptyState } from '@/components/ui/empty-state';
import { Screen } from '@/components/ui/screen';
import { SearchBar } from '@/components/ui/search-bar';
import { Gutter, Radius, Spacing } from '@/constants/theme';
import { CATEGORIES, categoryIcon } from '@/constants/topics';
import { searchTopics } from '@/db/topics';
import { useStartSession } from '@/hooks/use-start-session';
import { useTheme } from '@/hooks/use-theme';
import type { Category, TopicListItem } from '@/types/models';

export default function TopicsScreen() {
  const theme = useTheme();
  const db = useSQLiteContext();
  const startSession = useStartSession();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<Category | null>(null);
  const [topics, setTopics] = useState<TopicListItem[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      searchTopics(db, query, category).then((rows) => !cancelled && setTopics(rows));
    }, 150);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [db, query, category]);

  return (
    <Screen edges={['top']}>
      <View style={styles.header}>
        <ThemedText type="title">Topics</ThemedText>
        <ThemedText themeColor="textSecondary">Pick something you&apos;d like to talk about.</ThemedText>
      </View>

      <SearchBar value={query} onChangeText={setQuery} placeholder="Search topics" />

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chips}
        style={styles.chipsRow}>
        <Chip label="All" selected={!category} onPress={() => setCategory(null)} />
        {CATEGORIES.map((c) => (
          <Chip
            key={c.name}
            label={c.name}
            selected={category === c.name}
            onPress={() => setCategory(category === c.name ? null : c.name)}
          />
        ))}
      </ScrollView>

      {topics && topics.length === 0 ? (
        <EmptyState
          icon="search-off"
          title={query || category ? 'No matching topics' : 'No topics yet'}
          message={
            query || category
              ? 'Try a different word or category.'
              : 'Articles will appear here once they are added.'
          }
        />
      ) : null}

      {topics?.map((t) => (
        <Card key={t.id} tone="raised" onPress={() => startSession(t.id)} accessibilityLabel={`Start ${t.title}`} style={styles.card}>
          <View style={styles.row}>
            <View style={[styles.icon, { backgroundColor: theme.tintStrong }]}>
              <MaterialIcons name={categoryIcon(t.category)} size={22} color={theme.accentText} />
            </View>
            <View style={styles.text}>
              <ThemedText type="subtitle">{t.title}</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                {t.category} · {t.readMinutes} min read
              </ThemedText>
            </View>
            <MaterialIcons name="chevron-right" size={24} color={theme.textSecondary} />
          </View>
          <ThemedText type="small" themeColor="textSecondary" numberOfLines={2}>
            {t.summary}
          </ThemedText>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: Spacing.one,
    paddingTop: Spacing.two,
  },
  chipsRow: {
    flexGrow: 0,
    marginHorizontal: -Gutter,
  },
  chips: {
    gap: Spacing.two,
    paddingHorizontal: Gutter,
  },
  card: {
    borderRadius: Radius.large - 4,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three - 4,
  },
  icon: {
    width: 44,
    height: 44,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    flex: 1,
  },
});
