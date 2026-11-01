import { useVideoPlayer, VideoView } from 'expo-video';
import { StyleSheet } from 'react-native';

import { Radius } from '@/constants/theme';

export function RecordingPlayer({ uri }: { uri: string }) {
  const player = useVideoPlayer({ uri });

  return <VideoView player={player} style={styles.video} nativeControls contentFit="contain" />;
}

const styles = StyleSheet.create({
  video: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: Radius.medium,
    backgroundColor: '#000',
  },
});
