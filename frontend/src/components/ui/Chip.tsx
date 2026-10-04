import type { ReactNode } from 'react'
import './Chip.css'

interface ChipProps {
  selected?: boolean
  onClick?: () => void
  children: ReactNode
  /** sm = 36px on mobile, 40px on desktop · md = 40px · lg = 48px. */
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

/** Selectable pill (categories, durations, sort, examples). */
export function Chip({ selected = false, onClick, children, size = 'md', className }: ChipProps) {
  return (
    <button
      type="button"
      className={['chip', `chip--${size}`, selected && 'chip--selected', className]
        .filter(Boolean)
        .join(' ')}
      aria-pressed={selected}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
