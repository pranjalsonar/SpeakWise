import type { ReactNode } from 'react'
import './StickyActionBar.css'

/** Mobile-only bottom bar holding a step's primary action. Hidden on desktop (actions move to the rail). */
export function StickyActionBar({ children }: { children: ReactNode }) {
  return <div className="sticky-action-bar">{children}</div>
}
