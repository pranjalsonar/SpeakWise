import type { LandingFeature } from '@/core/types'
import { FeatureCard } from './FeatureCard'
import './Features.css'

export function Features({ features }: { features: LandingFeature[] }) {
  return (
    <section id="features" className="features" aria-labelledby="features-title">
      <h2 id="features-title" className="features__title">
        Why SpeakWise?
      </h2>
      <div className="features__grid">
        {features.map((feature) => (
          <FeatureCard key={feature.title} feature={feature} />
        ))}
      </div>
    </section>
  )
}
