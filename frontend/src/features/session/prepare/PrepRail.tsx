import { KeyPointsList } from '@/components/shared/KeyPointsList'
import { Button } from '@/components/ui/Button'
import { formatClock } from '@/core/utils'
import { TextSizeControl } from './TextSizeControl'
import './PrepRail.css'

interface PrepRailProps {
  secondsLeft: number
  readPct: number
  keyPoints: string[]
  textStep: number
  onTextStep: (step: number) => void
  notes: string
  onNotes: (notes: string) => void
  onReady: () => void
}

/** Desktop right rail: timer + progress tiles, key points, text size, notes and the CTA. */
export function PrepRail({
  secondsLeft,
  readPct,
  keyPoints,
  textStep,
  onTextStep,
  notes,
  onNotes,
  onReady,
}: PrepRailProps) {
  return (
    <aside className="prep-rail" aria-label="Preparation tools">
      <div className="prep-rail__tiles">
        <div className="prep-rail__tile">
          <span className="prep-rail__tile-value" role="timer" aria-label="Suggested time left">
            {formatClock(secondsLeft)}
          </span>
          <span className="prep-rail__tile-label">suggested time left</span>
        </div>
        <div className="prep-rail__tile">
          <span className="prep-rail__tile-value">{readPct}%</span>
          <span className="prep-rail__tile-label">read</span>
        </div>
      </div>

      <section className="prep-rail__section" aria-labelledby="rail-keys">
        <h2 id="rail-keys" className="prep-rail__heading">
          Key points to cover
        </h2>
        <KeyPointsList points={keyPoints} />
      </section>

      <div className="prep-rail__row">
        <span className="prep-rail__heading">Text size</span>
        <TextSizeControl step={textStep} onChange={onTextStep} tone="raised" />
      </div>

      <label className="prep-rail__notes">
        <span className="prep-rail__heading">Notes</span>
        <textarea
          className="prep-rail__notes-input"
          value={notes}
          onChange={(e) => onNotes(e.target.value)}
          placeholder="Jot down facts or phrases to use in your talk…"
        />
      </label>

      <Button size="lg" block onClick={onReady}>
        I'm ready, start talk
      </Button>
    </aside>
  )
}
