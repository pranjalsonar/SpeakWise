import type { ButtonHTMLAttributes, ReactNode } from 'react'
import './IconButton.css'

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  /** Required: icon-only buttons need an accessible name. */
  'aria-label': string
  icon: ReactNode
  size?: 40 | 44 | 48
  tone?: 'outline' | 'surface' | 'dark' | 'plain'
}

export function IconButton({
  icon,
  size = 44,
  tone = 'outline',
  className,
  type = 'button',
  ...rest
}: IconButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      className={['icon-btn', `icon-btn--${size}`, `icon-btn--${tone}`, className]
        .filter(Boolean)
        .join(' ')}
    >
      {icon}
    </button>
  )
}
