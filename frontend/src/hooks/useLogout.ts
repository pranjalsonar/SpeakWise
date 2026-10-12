import { useCallback } from 'react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { useAuth } from '@/context/AuthContext'

/** Signs out (revokes the token, clears the session) and goes to the login page. */
export function useLogout(): () => void {
  const { logout } = useAuth()
  const navigate = useNavigate()

  return useCallback(() => {
    logout()
    navigate(ROUTES.login, { replace: true })
  }, [logout, navigate])
}
