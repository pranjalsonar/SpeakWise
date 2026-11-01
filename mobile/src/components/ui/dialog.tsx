import { MaterialIcons } from '@expo/vector-icons';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ComponentProps, type ReactNode } from 'react';
import { BackHandler, Pressable, StyleSheet, View } from 'react-native';
import Animated, { Easing, FadeIn, FadeOut, Keyframe, ReduceMotion } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { EASE_OUT } from '@/constants/motion';
import { Gutter, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export type DialogAction = {
  label: string;
  /** default: primary button · destructive: danger · cancel: secondary, also used for back/scrim tap */
  style?: 'default' | 'destructive' | 'cancel';
  onPress?: () => void | Promise<void>;
};

export type DialogOptions = {
  title: string;
  message?: string;
  icon?: ComponentProps<typeof MaterialIcons>['name'];
  tone?: 'neutral' | 'danger';
  actions: DialogAction[];
};

type DialogContextValue = { show: (options: DialogOptions) => void };

const DialogContext = createContext<DialogContextValue | null>(null);

// iOS-style sheet curve in; a quicker ease-out out (exits are faster than entrances).
const SHEET_IN = new Keyframe({
  0: { transform: [{ translateY: 360 }] },
  100: { transform: [{ translateY: 0 }], easing: Easing.bezier(0.32, 0.72, 0, 1) },
})
  .duration(300)
  .reduceMotion(ReduceMotion.System);
const SHEET_OUT = new Keyframe({
  0: { transform: [{ translateY: 0 }] },
  100: { transform: [{ translateY: 360 }], easing: EASE_OUT },
})
  .duration(200)
  .reduceMotion(ReduceMotion.System);
const SCRIM_IN = FadeIn.duration(200);
const SCRIM_OUT = FadeOut.duration(160);

/**
 * Themed replacement for Alert.alert: a bottom sheet (the handoff's mobile ConfirmDialog).
 * Mount once at the root; call `useDialog().show({...})` anywhere.
 */
export function DialogProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<DialogOptions | null>(null);
  const show = useCallback((options: DialogOptions) => setCurrent(options), []);
  const value = useMemo(() => ({ show }), [show]);

  return (
    <DialogContext.Provider value={value}>
      <View style={styles.fill}>
        {children}
        {current ? <DialogSheet options={current} onDone={() => setCurrent(null)} /> : null}
      </View>
    </DialogContext.Provider>
  );
}

export function useDialog() {
  const ctx = useContext(DialogContext);
  if (!ctx) throw new Error('useDialog must be used inside <DialogProvider>');
  return ctx;
}

function DialogSheet({ options, onDone }: { options: DialogOptions; onDone: () => void }) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const cancel = options.actions.find((a) => a.style === 'cancel');
  // Primary choices first, the safe "cancel" choice last (closest to the thumb's resting place).
  const ordered = [...options.actions.filter((a) => a.style !== 'cancel'), ...(cancel ? [cancel] : [])];

  const choose = (action?: DialogAction) => {
    onDone();
    action?.onPress?.();
  };

  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      choose(cancel);
      return true;
    });
    return () => sub.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options]);

  const danger = options.tone === 'danger';

  return (
    <View style={StyleSheet.absoluteFill} accessibilityViewIsModal>
      <Animated.View entering={SCRIM_IN} exiting={SCRIM_OUT} style={[StyleSheet.absoluteFill, styles.scrim]}>
        <Pressable accessibilityLabel="Close dialog" style={StyleSheet.absoluteFill} onPress={() => choose(cancel)} />
      </Animated.View>

      <Animated.View
        entering={SHEET_IN}
        exiting={SHEET_OUT}
        accessibilityRole="alert"
        style={[styles.sheet, { backgroundColor: theme.background, paddingBottom: Spacing.four + insets.bottom }]}>
        <View style={[styles.grabber, { backgroundColor: theme.backgroundSelected }]} />
        {options.icon ? (
          <View style={[styles.icon, { backgroundColor: danger ? theme.dangerTint : theme.tintStrong }]}>
            <MaterialIcons name={options.icon} size={28} color={danger ? theme.danger : theme.accentText} />
          </View>
        ) : null}
        <ThemedText type="title" style={styles.title}>
          {options.title}
        </ThemedText>
        {options.message ? (
          <ThemedText themeColor="textSecondary" style={styles.message}>
            {options.message}
          </ThemedText>
        ) : null}
        <View style={styles.actions}>
          {ordered.map((a) => (
            <Button
              key={a.label}
              title={a.label}
              variant={a.style === 'cancel' ? 'secondary' : a.style === 'destructive' ? 'dangerSolid' : 'primary'}
              onPress={() => choose(a)}
            />
          ))}
        </View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: {
    flex: 1,
  },
  scrim: {
    backgroundColor: 'rgba(31, 29, 26, 0.55)',
  },
  sheet: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    borderTopLeftRadius: Radius.xl,
    borderTopRightRadius: Radius.xl,
    paddingHorizontal: Gutter + 4,
    paddingTop: Spacing.three - 4,
    gap: Spacing.three - 4,
  },
  grabber: {
    alignSelf: 'center',
    width: 44,
    height: 5,
    borderRadius: Radius.pill,
    marginBottom: Spacing.two,
  },
  icon: {
    width: 56,
    height: 56,
    borderRadius: Radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    lineHeight: 29,
  },
  message: {
    marginTop: -Spacing.one,
  },
  actions: {
    gap: Spacing.two + 2,
    marginTop: Spacing.three - 4,
  },
});
