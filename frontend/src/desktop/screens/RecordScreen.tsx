import { useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Banner } from '@/components/ui/Banner'
import { Spinner } from '@/components/ui/Spinner'
import { bridge } from '../bridge'
import type { ActiveSession } from '../DesktopApp'

// MP4 first; anything else is converted to MP4 by the main process (packaged ffmpeg).
const MIME_CANDIDATES = [
  'video/mp4;codecs=avc1.42E01E,mp4a.40.2',
  'video/mp4',
  'video/webm;codecs=vp9,opus',
  'video/webm;codecs=vp8,opus',
  'video/webm',
]

type Phase = 'starting' | 'preview' | 'recording' | 'finalizing' | 'consent' | 'error'

function mediaErrorMessage(e: unknown): string {
  const name = (e as DOMException)?.name
  if (name === 'NotAllowedError') return 'Camera or microphone permission was denied. Allow access and try again.'
  if (name === 'NotFoundError') return 'No camera or microphone was found. Connect one and try again.'
  if (name === 'NotReadableError') return 'The camera or microphone is in use by another application.'
  return `Could not open the camera and microphone (${name || 'unknown error'}).`
}

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`

interface Props {
  session: ActiveSession
  onSubmitted: () => void
  onCancel: () => void
}

export function RecordScreen({ session, onSubmitted, onCancel }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const [phase, setPhase] = useState<Phase>('starting')
  const [error, setError] = useState<string | null>(null)
  const [remaining, setRemaining] = useState(session.durationS)
  const [recordedS, setRecordedS] = useState<number | null>(null)
  const [attempt, setAttempt] = useState(0)

  const fail = (message: string) => {
    recorderRef.current = null
    setError(message)
    setPhase('error')
  }

  // Open camera + microphone.
  useEffect(() => {
    let cancelled = false
    navigator.mediaDevices
      .getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: true })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        if (!stream.getVideoTracks().length || !stream.getAudioTracks().length) {
          stream.getTracks().forEach((t) => t.stop())
          fail('Both a camera and a microphone are required.')
          return
        }
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
        setPhase('preview')
      })
      .catch((e) => !cancelled && fail(mediaErrorMessage(e)))
    return () => {
      cancelled = true
      const recorder = recorderRef.current
      recorderRef.current = null
      if (recorder?.state === 'recording') recorder.stop()
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [attempt])

  const start = () => {
    const stream = streamRef.current
    if (!stream) return
    const mimeType = MIME_CANDIDATES.find((t) => MediaRecorder.isTypeSupported(t))
    let recorder: MediaRecorder
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    } catch {
      fail('This computer cannot record audio and video together.')
      return
    }
    const chunks: Blob[] = []
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data)
    }
    recorder.onerror = () => fail('Recording failed. Try again.')
    recorder.onstop = async () => {
      if (recorderRef.current !== recorder) return // cancelled or failed
      recorderRef.current = null
      setPhase('finalizing')
      const blob = new Blob(chunks, { type: recorder.mimeType || mimeType || 'video/webm' })
      if (blob.size === 0) {
        fail('The recording is empty. Check the camera and microphone and try again.')
        return
      }
      const bytes = new Uint8Array(await blob.arrayBuffer())
      const res = await bridge().saveRecording(session.sessionId, bytes, blob.type)
      if (!res.ok) {
        fail(res.error)
        return
      }
      setRecordedS(res.durationS)
      streamRef.current?.getTracks().forEach((t) => t.stop())
      setPhase('consent')
    }
    // A device unplugged mid-recording ends its track.
    stream.getTracks().forEach((t) => (t.onended = () => recorderRef.current === recorder && fail('A camera or microphone was disconnected during recording.')))

    recorderRef.current = recorder
    recorder.start(1000)
    const startedAt = performance.now()
    setRemaining(session.durationS)
    setPhase('recording')
    const timer = window.setInterval(() => {
      const left = session.durationS - (performance.now() - startedAt) / 1000
      if (recorderRef.current !== recorder) {
        window.clearInterval(timer)
        return
      }
      if (left <= 0) {
        window.clearInterval(timer)
        recorder.stop()
        return
      }
      setRemaining(Math.ceil(left))
    }, 250)
  }

  const retry = () => {
    setError(null)
    setPhase('starting')
    setAttempt((n) => n + 1)
  }

  return (
    <section className="dk-record">
      <div className="dk-camera">
        <video ref={videoRef} autoPlay muted playsInline />
        {phase === 'recording' && (
          <div className="dk-rec-badge">
            <span className="dk-rec-dot" /> REC {fmt(remaining)}
          </div>
        )}
        {(phase === 'starting' || phase === 'finalizing') && (
          <div className="dk-camera__overlay">
            <Spinner size={28} />
            <p>{phase === 'starting' ? 'Opening camera and microphone…' : 'Finalising the MP4 recording…'}</p>
          </div>
        )}
      </div>

      <aside className="dk-record__side">
        <h1>Speak about the topic</h1>
        <p className="dk-muted">{session.topic.title}</p>
        <p>
          Duration: <strong>{fmt(session.durationS)}</strong>. Keep your face and both shoulders in frame and look
          toward the camera.
        </p>

        {error && <Banner>{error}</Banner>}

        {phase === 'preview' && (
          <Button size="lg" onClick={start}>
            Start recording
          </Button>
        )}
        {phase === 'recording' && <p className="dk-muted">Recording stops automatically at 0:00.</p>}
        {phase === 'consent' && (
          <div className="dk-consent">
            <p>
              Recorded {recordedS != null ? fmt(recordedS) : ''}. To analyse it, SpeakWise will upload the recording,
              the topic and the reading text to the &ldquo;SpeakWise Desktop&rdquo; folder in your Google Drive, where
              your Colab notebook processes it. The files are removed from Drive when you finish or discard the session.
            </p>
            <Button size="lg" onClick={onSubmitted}>
              Upload and analyse
            </Button>
          </div>
        )}
        {phase === 'error' && <Button onClick={retry}>Try again</Button>}
        {phase !== 'recording' && phase !== 'finalizing' && (
          <Button variant="ghost" onClick={onCancel}>
            Discard and go back
          </Button>
        )}
      </aside>
    </section>
  )
}
