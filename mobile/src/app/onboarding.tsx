import { StyleSheet, View } from 'react-native';
import Animated from 'react-native-reanimated';

import { BrandMark } from '@/components/brand-mark';
import { ProfileForm } from '@/components/profile-form';
import { ThemedText } from '@/components/themed-text';
import { Badge } from '@/components/ui/badge';
import { Screen } from '@/components/ui/screen';
import { enterUp, STAGGER_MS } from '@/constants/motion';
import { Spacing } from '@/constants/theme';
import { useProfile } from '@/context/profile-context';

// First launch only, so it can afford a small staggered entrance.
const HERO_ENTER = enterUp(0);
const FORM_ENTER = enterUp(STAGGER_MS * 2);

export default function OnboardingScreen() {
  const { saveProfile } = useProfile();

  return (
    <Screen>
      <Animated.View entering={HERO_ENTER} style={styles.hero}>
        <View style={styles.logo}>
          <BrandMark size={72} />
        </View>
        <Badge label="AI public-speaking coach" />
        <ThemedText type="title">Welcome to SpeakWise</ThemedText>
        <ThemedText themeColor="textSecondary">
          Read a short article, speak about it for 1–2 minutes, and get feedback on your delivery,
          body language and content. First, tell us a little about yourself.
        </ThemedText>
      </Animated.View>

      {/* Saving the profile flips the root Stack.Protected guard and moves to the tabs. */}
      <Animated.View entering={FORM_ENTER}>
        <ProfileForm submitLabel="Get started" onSubmit={saveProfile} />
      </Animated.View>

      <ThemedText type="small" themeColor="textSecondary" style={styles.note}>
        Your details stay on this phone and are only used to personalise the app.
      </ThemedText>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    gap: Spacing.two + 4,
    paddingTop: Spacing.four,
    paddingBottom: Spacing.two,
  },
  logo: {
    marginBottom: Spacing.two,
  },
  note: {
    textAlign: 'center',
  },
});
