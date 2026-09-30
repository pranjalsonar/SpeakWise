import { useEffect, useMemo, useReducer, type ReactNode } from 'react'
import {
  createInitialSession,
  sessionReducer,
  type SessionState,
} from '@/core/session/sessionReducer'
import { readJson, STORAGE_KEYS, writeJson } from '@/lib/storage'
import { SessionContext } from './SessionContext'

/** Restores the flow after a refresh. The recording blob URL can't survive a reload, so it's dropped. */
function restore(): SessionState {
  const saved = readJson<SessionState | null>(STORAGE_KEYS.session, null, 'session')
  if (!saved) return createInitialSession()
  const base = { ...createInitialSession(), ...saved, recording: null }
  // A review/processing step without its recording goes back to recording.
  return base.step === 'review' ? { ...base, step: 'record' } : base
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, dispatch] = useReducer(sessionReducer, undefined, restore)

  useEffect(() => {
    writeJson(STORAGE_KEYS.session, { ...session, recording: null }, 'session')
  }, [session])

  // Free the previous recording's memory when it's replaced or discarded.
  const recordingUrl = session.recording?.url
  useEffect(() => {
    return () => {
      if (recordingUrl?.startsWith('blob:')) URL.revokeObjectURL(recordingUrl)
    }
  }, [recordingUrl])

  const value = useMemo(() => ({ session, dispatch }), [session])
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}
