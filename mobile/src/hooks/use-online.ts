import { useNetInfo } from '@react-native-community/netinfo';

/** False only when we know the phone is offline (unknown counts as online). */
export function useOnline(): boolean {
  const { isConnected, isInternetReachable } = useNetInfo();
  return !(isConnected === false || isInternetReachable === false);
}
