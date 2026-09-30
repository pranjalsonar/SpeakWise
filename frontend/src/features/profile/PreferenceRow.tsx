import type { ReactNode } from 'react'
import './PreferenceRow.css'

interface PreferenceRowProps {
  label: string
  helper?: string
  /** Label and control on one line on mobile too (toggles). */
  inline?: boolean
  /** Tighter label-control gap on mobile (selects). */
  compact?: boolean
  children: ReactNode
}

/** Mobile: label above control. Desktop: label + helper left, control right, hairline between rows. */
export function PreferenceRow({
  label,
  helper,
  inline = false,
  compact = false,
  children,
}: PreferenceRowProps) {
  return (
    <div
      className={['pref-row', inline && 'pref-row--inline', compact && 'pref-row--compact']
        .filter(Boolean)
        .join(' ')}
    >
      <div className="pref-row__text">
        <span className="pref-row__label">{label}</span>
        {helper && <span className="pref-row__helper">{helper}</span>}
      </div>
      <div className="pref-row__control">{children}</div>
    </div>
  )
}
