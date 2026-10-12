import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import * as authApi from '@/api/api.auth'
import { clearAccessToken, onUnauthorized, tokenTimeLeftMs } from '@/api/authToken'
import { authService } from '@/core/services'
import type { User } from '@/core/types'
import { readJson, removeKey, STORAGE_KEYS, writeJson } from '@/lib/storage'
import { AuthContext, type AuthContextValue } from './AuthContext'

// The signed-in user lives in sessionStorage next to the token (see api/authToken.ts),
// so both are cleared together when the tab closes.

/** A saved user only counts while their access token is still valid. */
function restoreUser(): User | null {
  if (tokenTimeLeftMs() > 0) return readJson<User | null>(STORAGE_KEYS.auth, null, 'session')
  clearAccessToken()
  removeKey(STORAGE_KEYS.auth, 'session')
  return null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(restoreUser)

  const signIn = useCallback((next: User) => {
    writeJson(STORAGE_KEYS.auth, next, 'session')
    setUser(next)
    return next
  }, [])

  const clearSession = useCallback(() => {
    clearAccessToken()
    removeKey(STORAGE_KEYS.auth, 'session')
    removeKey(STORAGE_KEYS.session, 'session')
    setUser(null)
  }, [])

  // TODO: switch to the backend once it has a register endpoint (mock for now, no token).
  const register = useCallback(
    async (name: string, email: string, password: string) =>
      signIn(await authService.register(name, email, password)),
    [signIn],
  )

  const logout = useCallback(() => {
    // authApi.logout() reads the token before its first await, so clearing the
    // local session right after is safe; the server-side revoke finishes in the background.
    void authApi.logout()
    clearSession()
  }, [clearSession])

  // Any API call rejected with 401 (expired/revoked token) signs the user out.
  useEffect(() => onUnauthorized(clearSession), [clearSession])

  // Sign out when the token expires while the app is open.
  useEffect(() => {
    if (!user) return
    const msLeft = tokenTimeLeftMs()
    if (msLeft <= 0) return // mock-registered users have no token
    const timer = window.setTimeout(clearSession, msLeft)
    return () => window.clearTimeout(timer)
  }, [user, clearSession])

  const value = useMemo<AuthContextValue>(
    () => ({ user, signIn, updateUser: signIn, register, logout }),
    [user, signIn, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
