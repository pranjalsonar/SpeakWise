import { preferencesService } from '@/core/services'
import type { DurationMin } from '@/core/types'
import './DurationPicker.css'

interface DurationPickerProps {
  value: DurationMin
  onChange: (value: DurationMin) => void
}

/** Three large duration tiles (1 · 3 · 5 min). */
export function DurationPicker({ value, onChange }: DurationPickerProps) {
  return (
    <div className="duration-picker">
      <span className="duration-picker__label" id="duration-label">
        Speaking duration
      </span>
      <div className="duration-picker__options" role="radiogroup" aria-labelledby="duration-label">
        {preferencesService.getDurations().map((d) => (
          <button
            key={d}
            type="button"
            role="radio"
            aria-checked={value === d}
            className={[
              'duration-picker__option',
              value === d && 'duration-picker__option--selected',
            ]
              .filter(Boolean)
              .join(' ')}
            onClick={() => onChange(d)}
          >
            {d} min
          </button>
        ))}
      </div>
      <p className="duration-picker__helper">You'll speak for this long after reading.</p>
    </div>
  )
}
