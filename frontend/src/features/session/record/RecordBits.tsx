import { Check, Mic, X } from 'lucide-react'
import './RecordBits.css'

/** "✓ Camera" / "✓ Microphone" device status pills. */
export function StatusPills({ camera, microphone }: { camera: boolean; microphone: boolean }) {
  const pills = [
    { label: camera ? 'Camera' : 'Camera off', ok: camera },
    { label: microphone ? 'Microphone' : 'Mic off', ok: microphone },
  ]
  return (
    <div className="rec-pills">
      {pills.map((pill) => (
        <span
          key={pill.label}
          className={`rec-pills__pill rec-pills__pill--${pill.ok ? 'ok' : 'off'}`}
        >
          {pill.ok ? <Check size={16} aria-hidden="true" /> : <X size={16} aria-hidden="true" />}
          {pill.label}
        </span>
      ))}
    </div>
  )
}

/** Live microphone meter: mic icon + 10 sage bars. */
export function MicMeter({ bars, size }: { bars: number[]; size: 'sm' | 'md' }) {
  return (
    <div className={`mic-meter mic-meter--${size}`} role="img" aria-label="Microphone level">
      <Mic size={size === 'sm' ? 16 : 20} aria-hidden="true" />
      {bars.map((height, i) => (
        <span key={i} className="mic-meter__bar" style={{ height: `${height}%` }} />
      ))}
    </div>
  )
}

/** Pulsing "● REC" pill. */
export function RecPill({ size }: { size: 'sm' | 'md' }) {
  return (
    <span className={`rec-pill rec-pill--${size}`}>
      <span className="rec-pill__dot" aria-hidden="true" />
      REC
    </span>
  )
}

/** Full-bleed "Get ready" 5→1 overlay. The numeral re-mounts each second to replay cdPop. */
export function CountdownOverlay({ count, size }: { count: number; size: 'sm' | 'md' }) {
  return (
    <div className={`countdown countdown--${size}`} role="timer" aria-live="assertive">
      <span className="countdown__label">Get ready</span>
      <span key={count} className="countdown__num">
        {count}
      </span>
    </div>
  )
}
