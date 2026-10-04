import { TEXT_STEP_MAX, TEXT_STEP_MIN } from '@/core/session/sessionReducer'
import './TextSizeControl.css'

interface TextSizeControlProps {
  step: number
  onChange: (step: number) => void
  /** Button fill: surface (mobile top bar) or raised (desktop rail). */
  tone: 'surface' | 'raised'
}

export function TextSizeControl({ step, onChange, tone }: TextSizeControlProps) {
  return (
    <div className={`text-size text-size--${tone}`} role="group" aria-label="Text size">
      <button
        type="button"
        className="text-size__btn"
        aria-label="Smaller text"
        disabled={step <= TEXT_STEP_MIN}
        onClick={() => onChange(step - 1)}
      >
        A−
      </button>
      <button
        type="button"
        className="text-size__btn text-size__btn--up"
        aria-label="Larger text"
        disabled={step >= TEXT_STEP_MAX}
        onClick={() => onChange(step + 1)}
      >
        A+
      </button>
    </div>
  )
}
