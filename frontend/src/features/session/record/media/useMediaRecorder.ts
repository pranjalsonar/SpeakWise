import { useCallback, useRef } from 'react'

const MIME_CANDIDATES = [
  'video/webm;codecs=vp9,opus',
  'video/webm;codecs=vp8,opus',
  'video/webm',
  'video/mp4', // Safari / iOS
]

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined') return undefined
  return MIME_CANDIDATES.find((type) => MediaRecorder.isTypeSupported(type))
}

export interface RecorderResult {
  blob: Blob
  mimeType: string
}

/** Thin wrapper over MediaRecorder: start, pause/resume (end-early dialog), stop → Blob. */
export function useMediaRecorder(stream: MediaStream | null) {
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const start = useCallback((): boolean => {
    if (!stream || typeof MediaRecorder === 'undefined') return false
    const mimeType = pickMimeType()
    try {
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.start(1000)
      recorderRef.current = recorder
      return true
    } catch {
      return false
    }
  }, [stream])

  const pause = useCallback(() => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.pause()
  }, [])

  const resume = useCallback(() => {
    if (recorderRef.current?.state === 'paused') recorderRef.current.resume()
  }, [])

  const stop = useCallback(
    () =>
      new Promise<RecorderResult | null>((resolve) => {
        const recorder = recorderRef.current
        if (!recorder || recorder.state === 'inactive') {
          resolve(null)
          return
        }
        recorder.onstop = () => {
          const mimeType = recorder.mimeType || 'video/webm'
          resolve({ blob: new Blob(chunksRef.current, { type: mimeType }), mimeType })
          recorderRef.current = null
        }
        recorder.stop()
      }),
    [],
  )

  return { start, pause, resume, stop }
}
