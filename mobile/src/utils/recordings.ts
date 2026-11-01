/** Recordings are kept in app-private storage (no storage permission needed) for History playback. */
import { Directory, File, Paths } from 'expo-file-system';

function recordingsDir(): Directory {
  const dir = new Directory(Paths.document, 'recordings');
  if (!dir.exists) dir.create({ intermediates: true });
  return dir;
}

/** Copies a camera/gallery file (in the cache) to permanent storage and returns its new URI. */
export async function keepRecording(tempUri: string, sessionId: number): Promise<string> {
  const source = new File(tempUri);
  const dest = new File(recordingsDir(), `session-${sessionId}-${Date.now()}.mp4`);
  await source.copy(dest);
  if (tempUri.includes('/cache/') || tempUri.includes('/Caches/')) {
    deleteRecording(tempUri);
  }
  return dest.uri;
}

export function deleteRecording(uri: string | null | undefined) {
  if (!uri) return;
  try {
    const f = new File(uri);
    if (f.exists) f.delete();
  } catch {
    // already gone
  }
}

export function recordingExists(uri: string | null | undefined): boolean {
  if (!uri) return false;
  try {
    return new File(uri).exists;
  } catch {
    return false;
  }
}

export function freeSpaceBytes(): number | null {
  try {
    return Paths.availableDiskSpace;
  } catch {
    return null;
  }
}
