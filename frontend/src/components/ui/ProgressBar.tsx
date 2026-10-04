import './ProgressBar.css'

interface ProgressBarProps {
  /** 0–100 */
  value: number
  label: string
  height?: 4 | 5 | 6 | 8
  tone?: 'accent' | 'sage' | 'light'
  track?: 'neutral' | 'dark' | 'none'
  /** Square ends, for full-width bars pinned under a top bar. */
  square?: boolean
  className?: string
}

export function ProgressBar({
  value,
  label,
  height = 8,
  tone = 'accent',
  track = 'neutral',
  square = false,
  className,
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, value))
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct)}
      className={[
        'progress',
        `progress--h${height}`,
        `progress--track-${track}`,
        square && 'progress--square',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <div className={`progress__fill progress__fill--${tone}`} style={{ width: `${pct}%` }} />
    </div>
  )
}
