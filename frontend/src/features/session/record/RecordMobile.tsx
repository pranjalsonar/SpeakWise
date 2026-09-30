import { useState } from 'react'
import { ChevronDown, ChevronUp, Square, X } from 'lucide-react'
import { formatClock } from '@/core/utils'
import { CameraNotice } from './CameraNotice'
import { CameraStage } from './CameraStage'
import { CountdownOverlay, MicMeter, RecPill, StatusPills } from './RecordBits'
import type { RecordSession } from './useRecordSession'
import './RecordMobile.css'

interface RecordMobileProps {
  rec: RecordSession
  keyPoints: string[]
  onExit: () => void
}

/** Mobile: full-screen portrait preview with controls overlaid. */
export function RecordMobile({ rec, keyPoints, onExit }: RecordMobileProps) {
  const { camera, phase } = rec
  const [cueOpen, setCueOpen] = useState(true)
  const deviceOk = camera.status === 'ready'

  return (
    <div className="record-mob">
      <CameraStage stream={camera.stream} hasVideo={camera.hasVideo} variant="fill" />

      <div className="record-mob__header">
        <button
          type="button"
          className="record-mob__exit"
          aria-label="Exit session"
          onClick={onExit}
        >
          <X size={20} />
        </button>
        <span className="record-mob__step">Step 3 of 4 · Record</span>
        {phase === 'live' && <RecPill size="sm" />}
      </div>

      {phase === 'check' && (
        <>
          <div className="record-mob__pills">
            <StatusPills
              camera={deviceOk && camera.hasVideo}
              microphone={deviceOk && camera.hasAudio}
            />
          </div>
          <div className="record-mob__bottom">
            <h1 className="record-mob__topic">{rec.topic.title}</h1>
            {deviceOk ? (
              <p className="record-mob__tips">
                Speaking for {formatClock(rec.totalSec)} · Look at the camera · Speak clearly · Find
                good light
              </p>
            ) : (
              <CameraNotice status={camera.status} onRetry={camera.retry} />
            )}
            <MicMeter bars={rec.micBars} size="sm" />
            <button
              type="button"
              className="record-mob__start"
              aria-label="Start recording"
              onClick={rec.startCountdown}
            >
              Start
            </button>
            <span className="record-mob__label">front camera · mirrored</span>
          </div>
        </>
      )}

      {phase === 'countdown' && <CountdownOverlay count={rec.count} size="sm" />}

      {phase === 'live' && (
        <>
          <div className="record-mob__timer-wrap">
            <span
              className={['record-mob__timer', rec.isFinal && 'record-mob__timer--final']
                .filter(Boolean)
                .join(' ')}
              role="timer"
            >
              {formatClock(rec.remainingSec)}
            </span>
            {rec.isFinal && <span className="record-mob__wrap-up">Wrap up now</span>}
            <span className="record-mob__elapsed" aria-hidden="true">
              <span className="record-mob__elapsed-fill" style={{ width: `${rec.elapsedPct}%` }} />
            </span>
          </div>

          <div className="record-mob__bottom record-mob__bottom--live">
            <div className="record-mob__cue">
              <button
                type="button"
                className="record-mob__cue-toggle"
                aria-expanded={cueOpen}
                onClick={() => setCueOpen((open) => !open)}
              >
                Cue card
                {cueOpen ? (
                  <ChevronDown size={16} aria-hidden="true" />
                ) : (
                  <ChevronUp size={16} aria-hidden="true" />
                )}
              </button>
              {cueOpen && (
                <ol className="record-mob__cue-list">
                  {keyPoints.map((point, i) => (
                    <li key={point}>
                      {i + 1}. {point}
                    </li>
                  ))}
                </ol>
              )}
            </div>
            <button
              type="button"
              className="record-mob__stop"
              aria-label="Stop recording"
              onClick={rec.requestStop}
            >
              <Square size={28} aria-hidden="true" />
            </button>
          </div>
        </>
      )}
    </div>
  )
}
