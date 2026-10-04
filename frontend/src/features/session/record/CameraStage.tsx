import { useEffect, useRef, type ReactNode } from 'react'
import './CameraStage.css'

interface CameraStageProps {
  stream: MediaStream | null
  hasVideo: boolean
  /** fill = full-screen mobile preview · framed = 16:9 desktop card. */
  variant: 'fill' | 'framed'
  showLabel?: boolean
  children?: ReactNode
}

/**
 * Mirrored front-camera preview with a dashed face guide.
 * Without a camera it shows the design's placeholder silhouette so the flow still works.
 */
export function CameraStage({
  stream,
  hasVideo,
  variant,
  showLabel = true,
  children,
}: CameraStageProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    video.srcObject = hasVideo ? stream : null
    if (hasVideo) void video.play().catch(() => undefined)
  }, [stream, hasVideo])

  return (
    <div className={`camera-stage camera-stage--${variant}`}>
      {hasVideo ? (
        <video
          ref={videoRef}
          className="camera-stage__video"
          muted
          playsInline
          autoPlay
          aria-label="Your camera preview"
        />
      ) : (
        <div className="camera-stage__placeholder" aria-hidden="true">
          <span className="camera-stage__head" />
          <span className="camera-stage__body" />
        </div>
      )}
      <span className="camera-stage__guide" aria-hidden="true" />
      {variant === 'fill' && <span className="camera-stage__fade" aria-hidden="true" />}
      {showLabel && variant === 'framed' && (
        <span className="camera-stage__label">front camera · mirrored</span>
      )}
      {children}
    </div>
  )
}
