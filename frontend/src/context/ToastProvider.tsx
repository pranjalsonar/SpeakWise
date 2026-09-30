import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Toast } from '@/components/ui/Toast'
import { ToastContext } from './ToastContext'

const TOAST_MS = 3500

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ id: number; message: string } | null>(null)

  const showToast = useCallback((message: string) => {
    setToast({ id: Date.now(), message })
  }, [])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(null), TOAST_MS)
    return () => window.clearTimeout(timer)
  }, [toast])

  const value = useMemo(() => ({ showToast }), [showToast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast && <Toast key={toast.id} message={toast.message} />}
    </ToastContext.Provider>
  )
}
