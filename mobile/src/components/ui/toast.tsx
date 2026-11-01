import { MaterialIcons } from '@expo/vector-icons';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Animated, { FadeOut, Keyframe, ReduceMotion } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { EASE_OUT } from '@/constants/motion';
import { Gutter, Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type ToastTone = 'success' | 'info' | 'error';
type Toast = { id: number; message: string; tone: ToastTone };
type ToastContextValue = { show: (message: string, tone?: ToastTone) => void };

const ToastContext = createContext<ToastContextValue | null>(null);

const HIDE_AFTER_MS = 3500;
/** Clears the bottom tab bar on tab screens; on full-screen flows it simply sits a little higher. */
const BOTTOM_OFFSET = 88;

const TOAST_IN = new Keyframe({
  0: { opacity: 0, transform: [{ translateY: 16 }] },
  100: { opacity: 1, transform: [{ translateY: 0 }], easing: EASE_OUT },
})
  .duration(240)
  .reduceMotion(ReduceMotion.System);
const TOAST_OUT = FadeOut.duration(160);

const ICONS = { success: 'check-circle', info: 'info-outline', error: 'error-outline' } as const;

/** Dark toast from the handoff (auto-hides after 3.5s, tap to dismiss). Mount once at the root. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null);
  const nextId = useRef(0);
  const show = useCallback((message: string, tone: ToastTone = 'success') => {
    nextId.current += 1;
    setToast({ id: nextId.current, message, tone });
  }, []);
  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={value}>
      <View style={styles.fill}>
        {children}
        {toast ? <ToastView key={toast.id} toast={toast} onHide={() => setToast(null)} /> : null}
      </View>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}

function ToastView({ toast, onHide }: { toast: Toast; onHide: () => void }) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  useEffect(() => {
    const t = setTimeout(onHide, HIDE_AFTER_MS);
    return () => clearTimeout(t);
  }, [onHide]);

  const iconColor = toast.tone === 'error' ? theme.timerFinal : toast.tone === 'success' ? '#aebf92' : '#f9f4ed';

  return (
    <Animated.View
      entering={TOAST_IN}
      exiting={TOAST_OUT}
      pointerEvents="box-none"
      style={[styles.wrap, { bottom: insets.bottom + BOTTOM_OFFSET }]}>
      <Pressable
        accessibilityRole="alert"
        accessibilityLiveRegion="polite"
        accessibilityHint="Tap to dismiss"
        onPress={onHide}
        style={styles.toast}>
        <MaterialIcons name={ICONS[toast.tone]} size={20} color={iconColor} />
        <ThemedText type="small" style={styles.text}>
          {toast.message}
        </ThemedText>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  fill: {
    flex: 1,
  },
  wrap: {
    position: 'absolute',
    left: Gutter,
    right: Gutter,
    alignItems: 'center',
  },
  toast: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two + 2,
    maxWidth: 520,
    paddingHorizontal: Spacing.three + 2,
    paddingVertical: Spacing.three - 2,
    borderRadius: Radius.pill,
    // Dark in both themes (neutral-900 / on-dark), as in the handoff.
    backgroundColor: '#2e2b25',
    boxShadow: '0 12px 32px rgba(46, 43, 37, 0.22)',
  },
  text: {
    flexShrink: 1,
    color: '#f9f4ed',
  },
});
