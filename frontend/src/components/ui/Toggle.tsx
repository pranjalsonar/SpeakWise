import './Toggle.css'

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  /** md = 52×32 (profile) · sm = 48×28 (admin status). */
  size?: 'sm' | 'md'
  /** `status` uses sage when on (admin); `accent` is the default. */
  tone?: 'accent' | 'status'
}

export function Toggle({ checked, onChange, label, size = 'md', tone = 'accent' }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      className={['toggle', `toggle--${size}`, `toggle--${tone}`, checked && 'toggle--on']
        .filter(Boolean)
        .join(' ')}
      onClick={() => onChange(!checked)}
    >
      <span className="toggle__knob" />
    </button>
  )
}
