import { createContext, useContext } from 'react'
import type { User } from '@/core/types'

export interface AuthContextValue {
  user: User | null
  /** Store the user returned by authApi.login() as the signed-in user. */
  signIn: (user: User) => User
  /** Replace the signed-in user's details (e.g. after loading or editing the profile). */
  updateUser: (user: User) => User
  register: (name: string, email: string, password: string) => Promise<User>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

/** For screens behind RequireAuth, where a user is guaranteed. */
export function useCurrentUser(): User {
  const { user } = useAuth()
  if (!user) throw new Error('useCurrentUser used outside an authenticated route')
  return user
}
