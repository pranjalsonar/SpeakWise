import type { ReactNode } from 'react'
import './EmptyState.css'

interface EmptyStateProps {
  /** Lucide icon element. It's sized by CSS (20px mobile, 28px desktop). */
  icon: ReactNode
  title: string
  body: ReactNode
  action?: ReactNode
  /** Dashed-border card (Home, mobile History) or plain (inside a desktop table card). */
  variant?: 'dashed' | 'plain'
  /** Desktop icon circle: lg 88px (Home) · md 72px (History). */
  size?: 'lg' | 'md'
}

/** Mobile: stacked and left-aligned. Desktop: icon · text · action in a row. */
export function EmptyState({
  icon,
  title,
  body,
  action,
  variant = 'dashed',
  size = 'lg',
}: EmptyStateProps) {
  return (
    <div className={`empty-state empty-state--${variant} empty-state--${size}`}>
      <span className="empty-state__icon" aria-hidden="true">
        {icon}
      </span>
      <div className="empty-state__text">
        <h2 className="empty-state__title">{title}</h2>
        <p className="empty-state__body">{body}</p>
      </div>
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  )
}
