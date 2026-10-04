import { createContext, useContext, type Dispatch } from 'react'
import type { SessionAction, SessionState } from '@/core/session/sessionReducer'

export interface SessionContextValue {
  session: SessionState
  dispatch: Dispatch<SessionAction>
}

export const SessionContext = createContext<SessionContextValue | null>(null)

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used inside <SessionProvider>')
  return ctx
}
