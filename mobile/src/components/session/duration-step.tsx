import { MaterialIcons } from '@expo/vector-icons';
import { StyleSheet, View } from 'react-native';

import { SessionHeader } from '@/components/session/session-header';
import type { StepProps } from '@/components/session/types';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Screen } from '@/components/ui/screen';
import { DURATION_OPTIONS } from '@/constants/config';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export function DurationStep({ session, topic, update, onClose }: StepProps) {
  const theme = useTheme();

  return (
    <View style={styles.root}>
      <SessionHeader title="Duration" step={2} onClose={onClose} />
      <Screen edges={['bottom']} footer={<Button title="Back to the article" variant="secondary" onPress={() => update({ stage: 'reading' })} />}>
        <View style={styles.header}>
          <ThemedText type="title">How long do you want to speak?</ThemedText>
          <ThemedText themeColor="textSecondary">
            Topic: <ThemedText type="smallBold">{topic.title}</ThemedText>. Recording stops automatically when time is up.
          </ThemedText>
        </View>

        {DURATION_OPTIONS.map((o) => {
          const selected = session.durationSec === o.seconds;
          return (
            <Card
              key={o.seconds}
              tone="raised"
              onPress={() => update({ durationSec: o.seconds, stage: 'ready_to_record' })}
              accessibilityLabel={`${o.label}. ${o.hint}`}
              style={[styles.option, selected ? { borderColor: theme.primary } : {}]}>
              <View style={[styles.icon, { backgroundColor: theme.tintStrong }]}>
                <MaterialIcons name="timer" size={28} color={theme.accentText} />
              </View>
              <View style={styles.text}>
                <ThemedText type="heading">{o.label}</ThemedText>
                <ThemedText type="small" themeColor="textSecondary">
                  {o.hint}
                </ThemedText>
              </View>
              <MaterialIcons name="chevron-right" size={26} color={theme.textSecondary} />
            </Card>
          );
        })}
      </Screen>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  header: {
    gap: Spacing.two,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three,
    borderWidth: 2,
    borderColor: 'transparent',
    borderRadius: Radius.medium + 4,
  },
  icon: {
    width: 56,
    height: 56,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    flex: 1,
    gap: 2,
  },
});
