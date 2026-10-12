import './Toggle.css'

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  /** md = 52×32 (profile) · sm = 48×28 (admin status). */
  size?: 'sm' | 'md'
  /** `status` uses sage when on (admin); `accent` is the default. */
  tone?: 'accent' | 'status'
  disabled?: boolean
  /** Tooltip, e.g. why the toggle is disabled. */
  title?: string
}

export function Toggle({
  checked,
  onChange,
  label,
  size = 'md',
  tone = 'accent',
  disabled = false,
  title,
}: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      title={title}
      className={['toggle', `toggle--${size}`, `toggle--${tone}`, checked && 'toggle--on']
        .filter(Boolean)
        .join(' ')}
      onClick={() => onChange(!checked)}
    >
      <span className="toggle__knob" />
    </button>
  )
}
