import { useSyncExternalStore } from 'react'

export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query)
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    },
    () => window.matchMedia(query).matches,
    () => false,
  )
}

/** Desktop layout starts at 768px (handoff § Breakpoint). */
export const DESKTOP_QUERY = '(min-width: 768px)'

export const useIsDesktop = () => useMediaQuery(DESKTOP_QUERY)
