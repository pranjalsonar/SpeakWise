import { useCallback, useRef, useState } from 'react'
import { useInterval } from './useInterval'

/**
 * Wall-clock countdown that can pause and resume (e.g. while a dialog is open).
 * Uses timestamps rather than counting ticks, so it doesn't drift.
 */
export function useCountdownClock(onDone: () => void) {
  const [remainingMs, setRemainingMs] = useState(0)
  const [running, setRunning] = useState(false)
  const endAt = useRef(0)
  const pausedRemaining = useRef(0)

  const start = useCallback((totalSec: number) => {
    endAt.current = Date.now() + totalSec * 1000
    setRemainingMs(totalSec * 1000)
    setRunning(true)
  }, [])

  const pause = useCallback(() => {
    pausedRemaining.current = Math.max(0, endAt.current - Date.now())
    setRemainingMs(pausedRemaining.current)
    setRunning(false)
  }, [])

  const resume = useCallback(() => {
    endAt.current = Date.now() + pausedRemaining.current
    setRunning(true)
  }, [])

  const stop = useCallback(() => setRunning(false), [])

  useInterval(
    () => {
      const left = Math.max(0, endAt.current - Date.now())
      setRemainingMs(left)
      if (left === 0) {
        setRunning(false)
        onDone()
      }
    },
    running ? 200 : null,
  )

  return { remainingSec: remainingMs / 1000, running, start, pause, resume, stop }
}
