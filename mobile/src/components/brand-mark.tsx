import { StyleSheet, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

import { ThemedText } from '@/components/themed-text';
import { Fonts, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

// Geometry from SpeakWise-Brand-Assets/03_splash_mark_1024x1024.svg (viewBox cropped to the mark).
const BUBBLE =
  'M 512 180 C 720 180 844 290 844 470 C 844 650 710 740 530 740 C 476 740 420 726 374 706 C 298 770 206 792 184 792 C 172 792 164 780 170 769 C 194 712 210 656 204 612 C 160 568 140 514 140 470 C 140 290 304 180 512 180 Z';
const BARS = [
  { x: 342, y: 420, h: 110 },
  { x: 426, y: 340, h: 230 },
  { x: 510, y: 295, h: 305 },
  { x: 594, y: 380, h: 175 },
];
const VIEWBOX = '130 170 724 632';
const ASPECT = 724 / 632;

/** The SpeakWise mark: terracotta speech bubble with a sound-wave cut-out. */
export function BrandMark({ size = 40, cutout }: { size?: number; cutout?: string }) {
  const theme = useTheme();
  return (
    <Svg width={size * ASPECT} height={size} viewBox={VIEWBOX} accessibilityElementsHidden importantForAccessibility="no">
      <Path d={BUBBLE} fill="#C67139" />
      {BARS.map((b) => (
        <Rect key={b.x} x={b.x} y={b.y} width={48} height={b.h} rx={24} fill={cutout ?? theme.background} />
      ))}
    </Svg>
  );
}

/** Horizontal lockup: mark + "SpeakWise" wordmark (Caprasimo). */
export function BrandLockup({ size = 30 }: { size?: number }) {
  return (
    <View accessible accessibilityRole="header" accessibilityLabel="SpeakWise" style={styles.lockup}>
      <BrandMark size={size} />
      <ThemedText style={[styles.wordmark, { fontSize: size * 0.82, lineHeight: size * 1.05 }]}>SpeakWise</ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  lockup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
  },
  wordmark: {
    fontFamily: Fonts.heading,
    letterSpacing: -0.3,
  },
});
