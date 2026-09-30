import './SegmentedControl.css'

interface SegmentedControlProps<T extends string> {
  label: string
  options: readonly T[]
  value: T
  onChange: (value: T) => void
  /** Stretch segments to fill the row (mobile). */
  fullWidth?: boolean
  size?: 'md' | 'lg'
  /** Track colour: surface (default) or raised (inside surface cards). */
  track?: 'surface' | 'raised'
  className?: string
}

/** Pill track (surface) with a dark filled active segment. */
export function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
  fullWidth = false,
  size = 'md',
  track = 'surface',
  className,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={[
        'segmented',
        `segmented--${size}`,
        `segmented--track-${track}`,
        fullWidth && 'segmented--full',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {options.map((option) => {
        const active = option === value
        return (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={active}
            className={['segmented__option', active && 'segmented__option--active']
              .filter(Boolean)
              .join(' ')}
            onClick={() => onChange(option)}
          >
            {option}
          </button>
        )
      })}
    </div>
  )
}
