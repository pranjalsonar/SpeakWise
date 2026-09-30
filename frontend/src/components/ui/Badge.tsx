import type { ReactNode } from 'react'
import type { Difficulty } from '@/core/types'
import './Badge.css'

export type BadgeTone =
  'beginner' | 'intermediate' | 'advanced' | 'processing' | 'category' | 'custom' | 'admin'

interface BadgeProps {
  tone: BadgeTone
  children: ReactNode
  size?: 'sm' | 'md'
  className?: string
}

export function Badge({ tone, children, size = 'md', className }: BadgeProps) {
  return (
    <span
      className={['badge', `badge--${tone}`, `badge--${size}`, className].filter(Boolean).join(' ')}
    >
      {children}
    </span>
  )
}

const difficultyTone: Record<Difficulty, BadgeTone> = {
  Beginner: 'beginner',
  Intermediate: 'intermediate',
  Advanced: 'advanced',
}

export function DifficultyBadge({
  difficulty,
  size,
}: {
  difficulty: Difficulty
  size?: 'sm' | 'md'
}) {
  return (
    <Badge tone={difficultyTone[difficulty]} size={size}>
      {difficulty}
    </Badge>
  )
}
