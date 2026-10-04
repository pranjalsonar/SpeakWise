import './Avatar.css'

interface AvatarProps {
  initials: string
  size?: 36 | 40 | 44 | 48 | 64 | 72 | 88
  tone?: 'sage' | 'accent' | 'raised'
  className?: string
}

export function Avatar({ initials, size = 40, tone = 'sage', className }: AvatarProps) {
  return (
    <span
      className={['avatar', `avatar--${size}`, `avatar--${tone}`, className]
        .filter(Boolean)
        .join(' ')}
      aria-hidden="true"
    >
      {initials}
    </span>
  )
}
