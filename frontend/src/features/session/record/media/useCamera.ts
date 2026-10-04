import { useCallback, useEffect, useRef, useState } from 'react'

export type CameraStatus = 'requesting' | 'ready' | 'denied' | 'unavailable' | 'error'

export interface CameraState {
  stream: MediaStream | null
  status: CameraStatus
  hasVideo: boolean
  hasAudio: boolean
  retry: () => void
}

const CONSTRAINTS: MediaStreamConstraints = {
  video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
  audio: { echoCancellation: true, noiseSuppression: true },
}

function statusFromError(error: unknown): CameraStatus {
  const name = error instanceof DOMException ? error.name : ''
  if (name === 'NotAllowedError' || name === 'SecurityError') return 'denied'
  if (name === 'NotFoundError' || name === 'OverconstrainedError') return 'unavailable'
  return 'error'
}

/**
 * Front camera + microphone via getUserMedia. Stops every track on unmount.
 * Needs HTTPS (localhost is exempt).
 */
export function useCamera(): CameraState {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [status, setStatus] = useState<CameraStatus>('requesting')
  const [attempt, setAttempt] = useState(0)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    let cancelled = false
    const request = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setStatus('unavailable')
        return
      }
      try {
        const media = await navigator.mediaDevices.getUserMedia(CONSTRAINTS)
        if (cancelled) {
          media.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = media
        setStream(media)
        setStatus('ready')
      } catch (error) {
        if (!cancelled) setStatus(statusFromError(error))
      }
    }
    void request()
    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [attempt])

  const retry = useCallback(() => {
    setStatus('requesting')
    setStream(null)
    setAttempt((n) => n + 1)
  }, [])

  return {
    stream,
    status,
    hasVideo: Boolean(stream?.getVideoTracks().length),
    hasAudio: Boolean(stream?.getAudioTracks().length),
    retry,
  }
}
