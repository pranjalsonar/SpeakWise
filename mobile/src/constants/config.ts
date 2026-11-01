import Constants from 'expo-constants';

export const DURATION_OPTIONS = [
  { seconds: 60, label: '1 minute', hint: 'A quick practice round' },
  { seconds: 120, label: '2 minutes', hint: 'Cover more of the talking points' },
] as const;

export const MIN_RECORDING_SEC = 5;
export const MAX_UPLOAD_SEC = 130;
export const MIN_FREE_BYTES = 200 * 1024 * 1024;
export const POLL_INTERVAL_MS = 2500;
export const BACKEND_PORT = 8000;
export const BACKEND_URL_KEY = 'backend_url';
export const APP_TOKEN_KEY = 'backend_access_key';
export const READER_FONT_KEY = 'reader_font_size';

/**
 * Default backend address, in order:
 * 1. `expo.extra.backendUrl` in app.json, baked into the APK at build time (tunnel or cloud URL);
 * 2. in development, the Expo dev server's host (laptop Wi-Fi IP, or localhost with `adb reverse`);
 * 3. localhost.
 * Users can always override it in Profile → Server.
 */
export function defaultBackendUrl(): string {
  const configured = (Constants.expoConfig?.extra as { backendUrl?: string } | undefined)?.backendUrl?.trim();
  if (configured) return configured.replace(/\/+$/, '');
  const host = Constants.expoConfig?.hostUri?.split(':')[0];
  return `http://${host || 'localhost'}:${BACKEND_PORT}`;
}
