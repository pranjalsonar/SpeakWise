import { RouterProvider } from 'react-router/dom'
import { AuthProvider } from '@/context/AuthProvider'
import { PreferencesProvider } from '@/context/PreferencesProvider'
import { SessionProvider } from '@/context/SessionProvider'
import { ToastProvider } from '@/context/ToastProvider'
import { router } from './router'

export function App() {
  return (
    <AuthProvider>
      <PreferencesProvider>
        <SessionProvider>
          <ToastProvider>
            <RouterProvider router={router} />
          </ToastProvider>
        </SessionProvider>
      </PreferencesProvider>
    </AuthProvider>
  )
}
