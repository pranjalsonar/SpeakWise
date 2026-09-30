import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { useSession } from '@/context/SessionContext'
import { useCountdownClock } from '@/core/hooks/useCountdownClock'
import { useInterval } from '@/core/hooks/useInterval'
import { COUNTDOWN_FROM, FINAL_SECONDS } from '@/core/session/sessionReducer'
import { useBeforeUnload } from '@/hooks/useBeforeUnload'
import { useCamera } from './media/useCamera'
import { useMediaRecorder } from './media/useMediaRecorder'
import { useMicLevel } from './media/useMicLevel'

export type RecordPhase = 'check' | 'countdown' | 'live'

/**
 * Record step state machine: check → countdown (5→1) → live → review.
 * Recording stops automatically at 0:00. "Stop" pauses both timer and recorder while
 * the "End early?" dialog is open.
 */
export function useRecordSession() {
  const navigate = useNavigate()
  const { session, dispatch } = useSession()
  const camera = useCamera()
  const recorder = useMediaRecorder(camera.stream)

  const totalSec = session.durationMin * 60
  const [phase, setPhase] = useState<RecordPhase>('check')
  const [count, setCount] = useState(COUNTDOWN_FROM)
  const [endDialogOpen, setEndDialogOpen] = useState(false)
  const finishing = useRef(false)
  const realRecording = useRef(false)

  const finish = useCallback(
    async (remainingSec: number) => {
      if (finishing.current) return
      finishing.current = true
      const result = realRecording.current ? await recorder.stop() : null
      dispatch({
        type: 'recorded',
        recording: {
          url: result ? URL.createObjectURL(result.blob) : '',
          mimeType: result?.mimeType ?? '',
          durationSec: Math.max(1, Math.round(totalSec - remainingSec)),
          simulated: !result,
        },
      })
      navigate(ROUTES.sessionReview)
    },
    [dispatch, navigate, recorder, totalSec],
  )

  const clock = useCountdownClock(() => void finish(0))

  // 5 → 4 → 3 → 2 → 1, one per second, then go live.
  useInterval(
    () => {
      if (count > 1) {
        setCount(count - 1)
        return
      }
      realRecording.current = recorder.start()
      clock.start(totalSec)
      setPhase('live')
    },
    phase === 'countdown' ? 1000 : null,
  )

  useBeforeUnload(phase !== 'check')
  const micBars = useMicLevel(camera.stream, phase !== 'countdown')

  const startCountdown = () => {
    setCount(COUNTDOWN_FROM)
    setPhase('countdown')
  }

  const requestStop = () => {
    clock.pause()
    recorder.pause()
    setEndDialogOpen(true)
  }

  const keepTalking = () => {
    setEndDialogOpen(false)
    recorder.resume()
    clock.resume()
  }

  const endNow = () => {
    setEndDialogOpen(false)
    void finish(clock.remainingSec)
  }

  const remainingSec = phase === 'live' ? clock.remainingSec : totalSec

  return {
    topic: session.topic!,
    camera,
    phase,
    count,
    totalSec,
    remainingSec,
    elapsedPct: ((totalSec - remainingSec) / totalSec) * 100,
    isFinal: phase === 'live' && remainingSec <= FINAL_SECONDS,
    micBars,
    endDialogOpen,
    startCountdown,
    requestStop,
    keepTalking,
    endNow,
  }
}

export type RecordSession = ReturnType<typeof useRecordSession>
