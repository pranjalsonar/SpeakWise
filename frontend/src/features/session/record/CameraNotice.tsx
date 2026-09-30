import type { CameraStatus } from './media/useCamera'
import './CameraNotice.css'

const MESSAGES: Record<Exclude<CameraStatus, 'ready'>, string> = {
  requesting: 'Allow camera and microphone access when your browser asks.',
  denied: 'Camera access is blocked. Allow it in your browser settings, or practise without video.',
  unavailable: 'No camera found. You can still practise; your talk just won’t be recorded.',
  error: 'The camera couldn’t start (another app may be using it). You can still practise.',
}

/** Shown on the camera check when there is no usable camera. Start still works (demo mode). */
export function CameraNotice({ status, onRetry }: { status: CameraStatus; onRetry: () => void }) {
  if (status === 'ready') return null
  return (
    <p className="camera-notice" role="status">
      {MESSAGES[status]}
      {status !== 'requesting' && (
        <button type="button" className="camera-notice__retry" onClick={onRetry}>
          Try again
        </button>
      )}
    </p>
  )
}
