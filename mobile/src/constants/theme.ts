/**
 * SpeakWise design tokens — the "Organic" design system from
 * Speakwise app design/design_handoff_speakwise (README + _ds/styles.css).
 * Light theme is the handoff verbatim; dark theme is the same warm family on the
 * handoff's camera/neutral-900 grounds.
 */

import '@/global.css';

import { Platform } from 'react-native';

export const Colors = {
  light: {
    text: '#201e1d',
    textSecondary: '#645c50', // neutral-700
    background: '#f5ead8', // page ground
    surface: '#ebddc5', // cards
    raised: '#f9f4ed', // neutral-100: inputs, list rows, tab bar, sticky bars
    backgroundElement: '#dcd3c4', // neutral-300: tracks
    backgroundSelected: '#c0b6a5', // neutral-400
    border: 'rgba(32, 30, 29, 0.16)', // divider
    primary: '#c67139', // accent
    primaryHover: '#b2622d', // accent-600
    primaryPressed: '#8c491a', // accent-700
    onPrimary: '#f9f4ed',
    secondary: '#728157', // sage-600
    tint: '#fff2eb', // accent-100
    tintStrong: '#ffe1d0', // accent-200
    tintText: '#8c491a', // accent-700 (accent-coloured text, AA)
    accentText: '#643312', // accent-800
    success: '#728157', // sage-600
    successTint: '#e1eecc', // sage-200
    successText: '#3d472b', // sage-800
    avatar: '#ccdbb2', // sage-300
    warning: '#b7791f',
    warningTint: '#f6e7cc',
    danger: '#b3402c',
    dangerTint: '#f7ddd6',
    dangerText: '#7d2a1b',
    highlight: '#ffc6a5', // accent-300 (filler words)
    highlightText: '#402310', // accent-900
    recording: '#ff5a3d',
    timerFinal: '#ff7a5f',
    camera: '#1f1d1a',
    onDark: '#f9f4ed',
    shadow: 'rgba(46, 43, 37, 0.16)',
  },
  dark: {
    text: '#f9f4ed',
    textSecondary: '#c0b6a5',
    background: '#1f1d1a',
    surface: '#2e2b25',
    raised: '#38342d',
    backgroundElement: '#474238',
    backgroundSelected: '#645c50',
    border: 'rgba(249, 244, 237, 0.14)',
    primary: '#d67f48',
    primaryHover: '#c67139',
    primaryPressed: '#b2622d',
    onPrimary: '#201e1d',
    secondary: '#aebf92',
    tint: '#402310',
    tintStrong: '#643312',
    tintText: '#f6a06b',
    accentText: '#ffc6a5',
    success: '#aebf92',
    successTint: '#272e1b',
    successText: '#ccdbb2',
    avatar: '#56633f',
    warning: '#e0a84a',
    warningTint: '#3a2a0b',
    danger: '#e9785f',
    dangerTint: '#3b1a14',
    dangerText: '#f7ddd6',
    highlight: '#643312',
    highlightText: '#ffe1d0',
    recording: '#ff5a3d',
    timerFinal: '#ff7a5f',
    camera: '#1f1d1a',
    onDark: '#f9f4ed',
    shadow: 'rgba(0, 0, 0, 0.45)',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;
export type Theme = { [K in ThemeColor]: string };

/** Loaded in the root layout with @expo-google-fonts. Use the family per weight (no fontWeight). */
export const Fonts = {
  heading: 'Caprasimo_400Regular', // headings AND button labels
  body: 'Figtree_400Regular',
  bodySemiBold: 'Figtree_600SemiBold',
  bodyBold: 'Figtree_700Bold',
  reading: 'Literata_400Regular', // article body only
  readingSemiBold: 'Literata_600SemiBold',
  mono: Platform.select({ ios: 'ui-monospace', default: 'monospace' }),
} as const;

/** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 */
export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const Gutter = 20; // mobile side padding

/** chips/rows 24 · cards 32 · large panels 36–44 · buttons/inputs/pills 999 */
export const Radius = {
  small: 12,
  medium: 24,
  large: 32,
  xl: 40,
  pill: 999,
} as const;

export const MaxContentWidth = 800;
