import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { authService } from '@/core/services'
import type { User } from '@/core/types'
import { readJson, removeKey, STORAGE_KEYS, writeJson } from '@/lib/storage'
import { AuthContext, type AuthContextValue } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() =>
    readJson<User | null>(STORAGE_KEYS.auth, null),
  )

  const signIn = useCallback((next: User) => {
    writeJson(STORAGE_KEYS.auth, next)
    setUser(next)
    return next
  }, [])

  const login = useCallback(
    async (email: string, password: string) => signIn(await authService.login(email, password)),
    [signIn],
  )

  const register = useCallback(
    async (name: string, email: string, password: string) =>
      signIn(await authService.register(name, email, password)),
    [signIn],
  )

  const logout = useCallback(() => {
    removeKey(STORAGE_KEYS.auth)
    removeKey(STORAGE_KEYS.session, 'session')
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, login, register, logout }),
    [user, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
