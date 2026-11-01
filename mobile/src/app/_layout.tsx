import { Caprasimo_400Regular } from '@expo-google-fonts/caprasimo';
import { Figtree_400Regular, Figtree_600SemiBold, Figtree_700Bold } from '@expo-google-fonts/figtree';
import { Literata_400Regular, Literata_600SemiBold } from '@expo-google-fonts/literata';
import { useFonts } from 'expo-font';
import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { SQLiteProvider } from 'expo-sqlite';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { useColorScheme } from 'react-native';
import { useReducedMotion } from 'react-native-reanimated';

import { DialogProvider } from '@/components/ui/dialog';
import { ToastProvider } from '@/components/ui/toast';
import { Colors } from '@/constants/theme';
import { ProfileProvider, useProfile } from '@/context/profile-context';
import { initDatabase } from '@/db/migrations';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const scheme = useColorScheme() === 'dark' ? 'dark' : 'light';
  const c = Colors[scheme];
  const base = scheme === 'dark' ? DarkTheme : DefaultTheme;
  const navTheme = {
    ...base,
    colors: { ...base.colors, primary: c.primary, background: c.background, card: c.raised, text: c.text, border: c.border },
  };

  return (
    <ThemeProvider value={navTheme}>
      <StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
      <SQLiteProvider databaseName="speakwise.db" onInit={initDatabase}>
        <ProfileProvider>
          {/* Themed dialogs and toasts render above every screen. */}
          <ToastProvider>
            <DialogProvider>
              <RootNavigator />
            </DialogProvider>
          </ToastProvider>
        </ProfileProvider>
      </SQLiteProvider>
    </ThemeProvider>
  );
}

function RootNavigator() {
  const { profile, loading } = useProfile();
  const [fontsLoaded, fontError] = useFonts({
    Caprasimo_400Regular,
    Figtree_400Regular,
    Figtree_600SemiBold,
    Figtree_700Bold,
    Literata_400Regular,
    Literata_600SemiBold,
  });
  // Native platform transitions; a plain fade when the user asked the system to reduce motion.
  const reducedMotion = useReducedMotion();
  // If fonts fail to load we still start the app with system fonts.
  const ready = !loading && (fontsLoaded || !!fontError);

  useEffect(() => {
    if (ready) SplashScreen.hideAsync();
  }, [ready]);

  if (!ready) return null;

  return (
    <Stack screenOptions={{ headerShown: false, animation: reducedMotion ? 'fade' : 'default' }}>
      <Stack.Protected guard={!profile}>
        <Stack.Screen name="onboarding" />
      </Stack.Protected>
      <Stack.Protected guard={!!profile}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="session/[id]" />
        <Stack.Screen name="report/[id]" />
      </Stack.Protected>
    </Stack>
  );
}
