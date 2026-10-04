import './Spinner.css'

interface SpinnerProps {
  size?: number
  /** Ring colour. Defaults to the current text colour. */
  tone?: 'current' | 'accent'
  label?: string
}

export function Spinner({ size = 16, tone = 'current', label }: SpinnerProps) {
  return (
    <span
      className={`spinner spinner--${tone}`}
      style={{ width: size, height: size }}
      role={label ? 'status' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  )
}
