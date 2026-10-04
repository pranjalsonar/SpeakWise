import { AudioLines, BookOpen, Shuffle, TrendingUp, type LucideIcon } from 'lucide-react'
import type { LandingFeature } from '@/core/types'
import './FeatureCard.css'

const icons: Record<LandingFeature['icon'], LucideIcon> = {
  shuffle: Shuffle,
  'audio-lines': AudioLines,
  'book-open': BookOpen,
  'trending-up': TrendingUp,
}

export function FeatureCard({ feature }: { feature: LandingFeature }) {
  const Icon = icons[feature.icon]
  return (
    <article className="feature-card">
      <span className="feature-card__icon" aria-hidden="true">
        <Icon size={24} />
      </span>
      <h3 className="feature-card__title">{feature.title}</h3>
      <p className="feature-card__text">{feature.description}</p>
    </article>
  )
}
