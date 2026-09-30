import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { preferencesService } from '@/core/services'
import type { Preferences } from '@/core/types'
import { readJson, STORAGE_KEYS, writeJson } from '@/lib/storage'
import { PreferencesContext } from './PreferencesContext'

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(() => ({
    ...preferencesService.getDefaultPreferences(),
    ...readJson<Partial<Preferences>>(STORAGE_KEYS.preferences, {}),
  }))

  const updatePreferences = useCallback((patch: Partial<Preferences>) => {
    setPreferences((prev) => {
      const next = { ...prev, ...patch }
      writeJson(STORAGE_KEYS.preferences, next)
      return next
    })
  }, [])

  const value = useMemo(
    () => ({ preferences, updatePreferences }),
    [preferences, updatePreferences],
  )

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>
}
