import { useRef, useState } from 'react'
import { Pause, Play } from 'lucide-react'
import { formatClock } from '@/core/utils'
import './VideoPlayer.css'

interface VideoPlayerProps {
  /** Object URL of the recording. Empty in demo mode (no camera). */
  src: string
  durationSec: number
}

/** Recorded clip with the design's big play button and a slim progress bar. */
export function VideoPlayer({ src, durationSec }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)
  const [currentSec, setCurrentSec] = useState(0)
  const canPlay = Boolean(src)

  const toggle = () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) void video.play()
    else video.pause()
  }

  const progress = durationSec > 0 ? Math.min(100, (currentSec / durationSec) * 100) : 0

  return (
    <div className="video-player">
      {canPlay && (
        <video
          ref={videoRef}
          className="video-player__video"
          src={src}
          playsInline
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onEnded={() => setPlaying(false)}
          onTimeUpdate={(e) => setCurrentSec(e.currentTarget.currentTime)}
        />
      )}
      <span className="video-player__label">
        {canPlay ? 'recorded clip' : 'recorded clip · demo (no camera)'}
      </span>

      <button
        type="button"
        className={['video-player__play', playing && 'video-player__play--hidden']
          .filter(Boolean)
          .join(' ')}
        aria-label={playing ? 'Pause' : 'Play recording'}
        disabled={!canPlay}
        onClick={toggle}
      >
        {playing ? <Pause size={28} /> : <Play size={28} />}
      </button>

      {playing && (
        <button
          type="button"
          className="video-player__surface"
          aria-label="Pause"
          onClick={toggle}
        />
      )}

      <div className="video-player__bar">
        <span className="video-player__time">{formatClock(currentSec)}</span>
        <span className="video-player__track" aria-hidden="true">
          <span className="video-player__fill" style={{ width: `${progress}%` }} />
        </span>
        <span className="video-player__time">{formatClock(durationSec)}</span>
      </div>
      <span className="video-player__badge">{formatClock(durationSec)}</span>
    </div>
  )
}
