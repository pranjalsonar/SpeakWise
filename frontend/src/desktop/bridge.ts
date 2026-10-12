// Types for the API exposed by desktop/preload.cjs.
export type Result<T = object> = ({ ok: true } & T) | { ok: false; error: string }

export interface ConnectionStatus {
  configured: boolean
  configHint: string | null
  authorized: boolean
  driveReady: boolean
  workerAlive: boolean
  heartbeatAgeS: number | null
  notebookUrl: string
  detail: string | null
}

export interface PollResult {
  envelope: unknown
  workerAlive: boolean
  heartbeatAgeS: number | null
}

export interface SpeakwiseBridge {
  connectionStatus(): Promise<Result<ConnectionStatus>>
  signIn(): Promise<Result>
  signOut(): Promise<Result>
  openNotebook(): Promise<Result>
  startSession(input: { topic: string; readingMaterial: string; durationS: number }): Promise<Result<{ sessionId: string }>>
  saveRecording(sessionId: string, bytes: Uint8Array, mimeType: string): Promise<Result<{ durationS: number; sizeBytes: number }>>
  submit(sessionId: string): Promise<Result>
  poll(sessionId: string): Promise<Result<PollResult>>
  importReport(sessionId: string): Promise<Result<{ envelope?: unknown; canceled?: boolean }>>
  finish(sessionId: string): Promise<Result>
}

declare global {
  interface Window {
    speakwise?: SpeakwiseBridge
  }
}

export function bridge(): SpeakwiseBridge {
  if (!window.speakwise) throw new Error('SpeakWise desktop bridge is unavailable. Start the app with Electron.')
  return window.speakwise
}
