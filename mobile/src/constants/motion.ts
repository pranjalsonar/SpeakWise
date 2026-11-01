/**
 * Motion tokens. Subtle by design: press feedback, step changes and the report reveal only.
 * Tab switches and frequent list updates deliberately do not animate.
 */
import { cubicBezier, Easing, Keyframe, ReduceMotion } from 'react-native-reanimated';

/** Strong ease-out for UI (Emil Kowalski's curve). Never ease-in on UI. */
export const EASE_OUT = Easing.bezier(0.23, 1, 0.32, 1);
export const EASE_OUT_CSS = cubicBezier(0.23, 1, 0.32, 1);

export const Duration = {
  press: 120,
  enter: 260,
  progress: 300,
  /** Rare moments only (the report score reveal). */
  reveal: 700,
} as const;

/** Fade up 8px. Skipped entirely when the system "reduce motion" setting is on. */
export function enterUp(delay = 0) {
  return new Keyframe({
    0: { opacity: 0, transform: [{ translateY: 8 }] },
    100: { opacity: 1, transform: [{ translateY: 0 }], easing: EASE_OUT },
  })
    .duration(Duration.enter)
    .delay(delay)
    .reduceMotion(ReduceMotion.System);
}

/** Plain fade, for swapping one step of a flow for the next. */
export const ENTER_FADE = new Keyframe({
  0: { opacity: 0 },
  100: { opacity: 1, easing: EASE_OUT },
})
  .duration(220)
  .reduceMotion(ReduceMotion.System);

/** Countdown digits: 0.9 → 1 with a fade (never from scale 0). */
export const ENTER_POP = new Keyframe({
  0: { opacity: 0, transform: [{ scale: 0.9 }] },
  100: { opacity: 1, transform: [{ scale: 1 }], easing: EASE_OUT },
})
  .duration(250)
  .reduceMotion(ReduceMotion.System);

/** Stagger between items that enter together (30–80ms). */
export const STAGGER_MS = 50;
