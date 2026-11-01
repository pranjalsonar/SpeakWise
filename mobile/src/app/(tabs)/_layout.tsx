import { NativeTabs } from 'expo-router/native-tabs';

import { useTheme } from '@/hooks/use-theme';

/** Tab bar on the raised neutral; active = accent-700 (handoff mobile app shell). */
export default function TabsLayout() {
  const theme = useTheme();

  return (
    <NativeTabs
      backgroundColor={theme.raised}
      indicatorColor={theme.tintStrong}
      iconColor={{ default: theme.textSecondary, selected: theme.tintText }}
      labelStyle={{ default: { color: theme.textSecondary }, selected: { color: theme.tintText } }}>
      <NativeTabs.Trigger name="index">
        <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon md="home" />
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="topics">
        <NativeTabs.Trigger.Label>Topics</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon md="menu_book" />
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="history">
        <NativeTabs.Trigger.Label>History</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon md="history" />
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="profile">
        <NativeTabs.Trigger.Label>Profile</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon md="person" />
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
