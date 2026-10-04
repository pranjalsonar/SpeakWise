import type { Metric } from '@/core/types'
import './MetricCard.css'

/** Bar colour: ≥80 sage · ≥70 accent · otherwise dark accent. */
const barTone = (score: number) => (score >= 80 ? 'good' : score >= 70 ? 'ok' : 'low')

export function MetricCard({ metric }: { metric: Metric }) {
  return (
    <article className="metric-card">
      <div className="metric-card__head">
        <h3 className="metric-card__name">{metric.name}</h3>
        <span className="metric-card__score">{metric.score}</span>
      </div>
      <div className="metric-card__track" aria-hidden="true">
        <span
          className={`metric-card__fill metric-card__fill--${barTone(metric.score)}`}
          style={{ width: `${metric.score}%` }}
        />
      </div>
      {metric.value && <p className="metric-card__value">{metric.value}</p>}
      <p className="metric-card__insight">{metric.insight}</p>
    </article>
  )
}
