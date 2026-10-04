import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useAuth } from '@/context/AuthContext'
import { useSession } from '@/context/SessionContext'
import { hasReached, type SessionStep } from '@/core/session/sessionReducer'
import type { Role } from '@/core/types'
import { homePathFor, ROUTES } from './routes'

/**
 * Signed-in users only. Otherwise go to /login and come back afterwards.
 * Admins may also open the student app ("Back to app"); students can't open /admin.
 */
export function RequireAuth({ role, children }: { role?: Role; children: ReactNode }) {
  const { user } = useAuth()
  const location = useLocation()
  if (!user) return <Navigate to={ROUTES.login} replace state={{ from: location.pathname }} />
  if (role && user.role !== role && user.role !== 'admin')
    return <Navigate to={homePathFor(user.role)} replace />
  return children
}

/**
 * Login/Register: signed-in users go back to the page that sent them to login
 * (if their role can open it), otherwise to their home.
 */
export function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const location = useLocation()
  if (!user) return children

  const from = (location.state as { from?: string } | null)?.from
  const isAdminPath = from?.startsWith(ROUTES.admin) ?? false
  const allowed = from && (user.role === 'admin' ? isAdminPath : !isAdminPath)
  return <Navigate to={allowed ? from : homePathFor(user.role)} replace />
}

/** Session steps can't be opened out of order (e.g. /session/record without a topic). */
export function RequireSessionStep({ step, children }: { step: SessionStep; children: ReactNode }) {
  const { session } = useSession()
  if (!hasReached(session, step)) return <Navigate to={ROUTES.sessionTopic} replace />
  return children
}
