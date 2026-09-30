import { useEffect } from 'react'

/** Asks the browser to confirm before closing/reloading the tab while `active` (e.g. mid-recording). */
export function useBeforeUnload(active: boolean) {
  useEffect(() => {
    if (!active) return
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault()
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [active])
}
