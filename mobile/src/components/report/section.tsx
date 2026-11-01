import { MaterialIcons } from '@expo/vector-icons';
import { useMemo, useState, type ComponentProps, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Animated from 'react-native-reanimated';

import { ThemedText } from '@/components/themed-text';
import { Card } from '@/components/ui/card';
import { enterUp, STAGGER_MS } from '@/constants/motion';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type SectionProps = {
  icon: ComponentProps<typeof MaterialIcons>['name'];
  title: string;
  children: ReactNode;
  /** Collapsible sections start closed. */
  collapsible?: boolean;
  /** Position in the report's entrance stagger; omit for sections below the fold. */
  enterIndex?: number;
};

export function Section({ icon, title, children, collapsible, enterIndex }: SectionProps) {
  const entering = useMemo(() => (enterIndex == null ? undefined : enterUp(enterIndex * STAGGER_MS)), [enterIndex]);
  return (
    <Animated.View entering={entering}>
      <SectionCard icon={icon} title={title} collapsible={collapsible}>
        {children}
      </SectionCard>
    </Animated.View>
  );
}

function SectionCard({ icon, title, children, collapsible }: Omit<SectionProps, 'enterIndex'>) {
  const theme = useTheme();
  const [open, setOpen] = useState(!collapsible);

  const header = (
    <View style={styles.header}>
      <MaterialIcons name={icon} size={22} color={theme.primary} />
      <ThemedText type="heading" style={styles.title}>
        {title}
      </ThemedText>
      {collapsible ? <MaterialIcons name={open ? 'expand-less' : 'expand-more'} size={24} color={theme.textSecondary} /> : null}
    </View>
  );

  return (
    <Card>
      {collapsible ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={title}
          accessibilityState={{ expanded: open }}
          hitSlop={{ top: 12, bottom: 12 }}
          onPress={() => setOpen((o) => !o)}>
          {header}
        </Pressable>
      ) : (
        header
      )}
      {open ? <View style={styles.body}>{children}</View> : null}
    </Card>
  );
}

/** Bulleted list used inside sections. */
export function Bullets({ items, icon = 'circle', color }: { items: string[]; icon?: ComponentProps<typeof MaterialIcons>['name']; color?: string }) {
  const theme = useTheme();
  return (
    <View style={styles.bullets}>
      {items.map((item) => (
        <View key={item} style={styles.bullet}>
          <MaterialIcons name={icon} size={icon === 'circle' ? 8 : 18} color={color ?? theme.primary} style={icon === 'circle' ? styles.dot : styles.iconTop} />
          <ThemedText style={styles.bulletText}>{item}</ThemedText>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
  },
  title: {
    flex: 1,
  },
  body: {
    gap: Spacing.three - 4,
    marginTop: Spacing.two,
  },
  bullets: {
    gap: Spacing.two,
  },
  bullet: {
    flexDirection: 'row',
    gap: Spacing.two,
  },
  dot: {
    marginTop: 9,
  },
  iconTop: {
    marginTop: 3,
  },
  bulletText: {
    flex: 1,
  },
});
