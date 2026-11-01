import { useFocusEffect, useRouter } from 'expo-router';
import { useSQLiteContext } from 'expo-sqlite';
import { useCallback, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { SessionRow } from '@/components/session-row';
import { ThemedText } from '@/components/themed-text';
import { Avatar, initialsOf } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Chip } from '@/components/ui/chip';
import { EmptyState } from '@/components/ui/empty-state';
import { Screen } from '@/components/ui/screen';
import { SearchBar } from '@/components/ui/search-bar';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Spacing } from '@/constants/theme';
import { useProfile } from '@/context/profile-context';
import { listHistory, type HistoryItem } from '@/db/sessions';

type Filter = 'all' | 'done' | 'failed';
type Sort = 'date' | 'score';

export default function HistoryScreen() {
  const db = useSQLiteContext();
  const router = useRouter();
  const { profile } = useProfile();
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [sort, setSort] = useState<Sort>('date');

  useFocusEffect(
    useCallback(() => {
      listHistory(db).then(setItems);
    }, [db])
  );

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (items ?? []).filter(
      (i) =>
        (filter === 'all' || i.stage === filter) &&
        (!q || i.topicTitle.toLowerCase().includes(q) || i.category.toLowerCase().includes(q))
    );
    // Score sort: highest first, failed sessions last.
    return sort === 'score' ? [...list].sort((a, b) => (b.overallScore ?? -1) - (a.overallScore ?? -1)) : list;
  }, [items, query, filter, sort]);

  const clear = () => {
    setQuery('');
    setFilter('all');
  };

  return (
    <Screen edges={['top']}>
      <View style={styles.topBar}>
        <ThemedText type="title">History</ThemedText>
        <Avatar initials={initialsOf(profile?.firstName, profile?.lastName)} onPress={() => router.navigate('/profile')} />
      </View>

      {items && items.length === 0 ? (
        <EmptyState
          icon="history"
          title="No sessions yet"
          message="Finish your first practice session and your report will be saved here."
          action={<Button title="Choose a topic" onPress={() => router.navigate('/topics')} />}
        />
      ) : (
        <>
          <SearchBar value={query} onChangeText={setQuery} placeholder="Search topics" />
          <SegmentedControl<Filter>
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'all', label: 'All' },
              { value: 'done', label: 'Completed' },
              { value: 'failed', label: 'Needs retry' },
            ]}
          />
          <View style={styles.sortRow}>
            <ThemedText themeColor="textSecondary" style={styles.flex}>
              {shown.length} {shown.length === 1 ? 'session' : 'sessions'}
            </ThemedText>
            <ThemedText themeColor="textSecondary">Sort</ThemedText>
            <Chip label="Date" selected={sort === 'date'} onPress={() => setSort('date')} />
            <Chip label="Score" selected={sort === 'score'} onPress={() => setSort('score')} />
          </View>

          {items && shown.length === 0 ? (
            <EmptyState
              icon="history"
              title="No sessions found"
              message="Try another search or filter."
              action={<Button title="Clear filters" variant="secondary" onPress={clear} />}
            />
          ) : null}

          {shown.map((item) => (
            <SessionRow
              key={item.id}
              item={item}
              onPress={() =>
                router.push(
                  item.stage === 'failed'
                    ? { pathname: '/session/[id]', params: { id: String(item.id) } }
                    : { pathname: '/report/[id]', params: { id: String(item.id) } }
                )
              }
            />
          ))}
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Spacing.two,
  },
  sortRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
  },
  flex: {
    flex: 1,
  },
});
