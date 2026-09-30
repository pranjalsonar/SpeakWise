import { AudioLines, Eye, Square, Sun } from 'lucide-react'
import { KeyPointsList } from '@/components/shared/KeyPointsList'
import { formatClock } from '@/core/utils'
import { CameraStage } from './CameraStage'
import { CameraNotice } from './CameraNotice'
import { CountdownOverlay, MicMeter, RecPill, StatusPills } from './RecordBits'
import type { RecordSession } from './useRecordSession'
import './RecordDesktop.css'

/** Desktop: 16:9 preview + controls row on the left, timer and cue card panel on the right. */
export function RecordDesktop({ rec, keyPoints }: { rec: RecordSession; keyPoints: string[] }) {
  const { camera, phase } = rec
  const deviceOk = camera.status === 'ready'

  return (
    <div className="record-desk">
      <div className="record-desk__main">
        <CameraStage stream={camera.stream} hasVideo={camera.hasVideo} variant="framed">
          {phase === 'check' && (
            <div className="record-desk__pills">
              <StatusPills
                camera={deviceOk && camera.hasVideo}
                microphone={deviceOk && camera.hasAudio}
              />
            </div>
          )}
          {phase === 'live' && (
            <div className="record-desk__rec">
              <RecPill size="md" />
            </div>
          )}
          {phase === 'countdown' && <CountdownOverlay count={rec.count} size="md" />}
        </CameraStage>

        <div className="record-desk__controls">
          <MicMeter bars={rec.micBars} size="md" />
          {phase === 'check' && (
            <>
              {deviceOk ? (
                <ul className="record-desk__tips">
                  <li>
                    <Eye size={16} aria-hidden="true" />
                    Look at the camera
                  </li>
                  <li>
                    <AudioLines size={16} aria-hidden="true" />
                    Speak clearly
                  </li>
                  <li>
                    <Sun size={16} aria-hidden="true" />
                    Find good light
                  </li>
                </ul>
              ) : (
                <CameraNotice status={camera.status} onRetry={camera.retry} />
              )}
              <button type="button" className="record-desk__start" onClick={rec.startCountdown}>
                Start
              </button>
            </>
          )}
          {phase === 'countdown' && <span className="record-desk__spacer" />}
          {phase === 'live' && (
            <>
              <div className="record-desk__elapsed" aria-hidden="true">
                <span
                  className="record-desk__elapsed-fill"
                  style={{ width: `${rec.elapsedPct}%` }}
                />
              </div>
              <button type="button" className="record-desk__stop" onClick={rec.requestStop}>
                <Square size={20} className="record-desk__stop-icon" aria-hidden="true" />
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      <aside className="record-desk__panel">
        <div className="record-desk__card">
          {phase === 'live' ? (
            <>
              <span
                className={['record-desk__timer', rec.isFinal && 'record-desk__timer--final']
                  .filter(Boolean)
                  .join(' ')}
                role="timer"
              >
                {formatClock(rec.remainingSec)}
              </span>
              <span
                className={
                  rec.isFinal ? 'record-desk__hint record-desk__hint--final' : 'record-desk__hint'
                }
              >
                {rec.isFinal
                  ? 'Final seconds, wrap up'
                  : `remaining of ${formatClock(rec.totalSec)}`}
              </span>
            </>
          ) : (
            <>
              <span className="record-desk__duration">{formatClock(rec.totalSec)}</span>
              <span className="record-desk__hint">
                {phase === 'check' ? 'Speaking time. Recording stops at 0:00.' : 'Starting…'}
              </span>
            </>
          )}
        </div>

        <div className="record-desk__card record-desk__card--grow">
          <p className="record-desk__overline">Your topic</p>
          <h1 className="record-desk__topic">{rec.topic.title}</h1>
          <p className="record-desk__cue-title">Cue card</p>
          <KeyPointsList points={keyPoints} tone="dark" />
        </div>
      </aside>
    </div>
  )
}
