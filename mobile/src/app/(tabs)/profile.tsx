import { useSQLiteContext } from 'expo-sqlite';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { ProfileForm } from '@/components/profile-form';
import { ServerSettings } from '@/components/server-settings';
import { Avatar, initialsOf } from '@/components/ui/avatar';
import { useDialog } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/toast';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Screen } from '@/components/ui/screen';
import { Spacing } from '@/constants/theme';
import { useProfile } from '@/context/profile-context';
import { deleteAllHistory } from '@/db/sessions';
import { useTheme } from '@/hooks/use-theme';
import type { ProfileInput } from '@/types/models';
import { deleteRecording } from '@/utils/recordings';

export default function ProfileScreen() {
  const theme = useTheme();
  const db = useSQLiteContext();
  const dialog = useDialog();
  const toast = useToast();
  const { profile, saveProfile } = useProfile();
  const [editing, setEditing] = useState(false);

  if (!profile) return null;

  const fullName = [profile.firstName, profile.lastName].filter(Boolean).join(' ');
  const initials = initialsOf(profile.firstName, profile.lastName);
  const rows: [string, string][] = [
    ['Age', profile.age != null ? String(profile.age) : '—'],
    ['Gender', profile.gender ?? '—'],
    ['Goal', profile.goal ?? '—'],
  ];

  const save = async (input: ProfileInput) => {
    await saveProfile(input);
    setEditing(false);
    toast.show('Profile updated');
  };

  const clearHistory = () =>
    dialog.show({
      icon: 'delete-sweep',
      tone: 'danger',
      title: 'Delete all history?',
      message: 'All sessions, reports and recordings will be removed from this phone. This cannot be undone.',
      actions: [
        {
          label: 'Delete everything',
          style: 'destructive',
          onPress: async () => {
            (await deleteAllHistory(db)).forEach(deleteRecording);
            toast.show('History cleared');
          },
        },
        { label: 'Cancel', style: 'cancel' },
      ],
    });

  return (
    <Screen edges={['top']}>
      <View style={styles.header}>
        <ThemedText type="title">Profile</ThemedText>
      </View>

      {editing ? (
        <ProfileForm initial={profile} submitLabel="Save changes" onSubmit={save} onCancel={() => setEditing(false)} />
      ) : (
        <>
          <Card style={styles.identity}>
            <Avatar initials={initials} size={72} />
            <ThemedText type="heading">{fullName}</ThemedText>
            <Button title="Edit profile" icon="edit" variant="secondary" onPress={() => setEditing(true)} style={styles.editBtn} />
          </Card>

          <Card tone="raised">
            {rows.map(([label, value], i) => (
              <View key={label} style={[styles.row, i > 0 && { borderTopColor: theme.border, borderTopWidth: StyleSheet.hairlineWidth }]}>
                <ThemedText themeColor="textSecondary">{label}</ThemedText>
                <ThemedText type="smallBold">{value}</ThemedText>
              </View>
            ))}
          </Card>

          <ThemedText type="caption" style={styles.sectionTitle}>
            Server
          </ThemedText>
          <Card tone="raised">
            <ServerSettings />
          </Card>

          <ThemedText type="caption" style={styles.sectionTitle}>
            Data
          </ThemedText>
          <Button title="Delete all history" variant="danger" onPress={clearHistory} />
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingTop: Spacing.three,
  },
  sectionTitle: {
    marginTop: Spacing.two,
  },
  identity: {
    alignItems: 'center',
    paddingVertical: Spacing.four,
  },
  editBtn: {
    alignSelf: 'stretch',
    marginTop: Spacing.two,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.two + 4,
  },
});
